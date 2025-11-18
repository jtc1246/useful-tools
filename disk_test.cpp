#include <fcntl.h>
#include <unistd.h>
#include <cstdlib>
#include <cstring>
#include <cstdio>
#include <errno.h>
#include <string>
#include <iostream>
#include <vector>
#include <cassert>
#include <thread>
#include <atomic>
#include <chrono>
#include <random>

#define PAGE_SIZE 4096
#define SEQUENTIAL_BLOCK_SIZE (4 * 1024 * 1024) // 4MB
using namespace std;

string FILE_NAME;
int SEQUENTIAL_READ_THREADS = 0;
int RANDOM_READ_THREADS = 0;
int SEQUENTIAL_WRITE_THREADS = 0;
int RANDOM_WRITE_THREADS = 0;
int ARENA_SIZE_GB = 0;
double TEST_TIME_SEC = 0;

thread_local char* THREAD_BUFFER = nullptr;

void init_thread_buffer() {
    if (!THREAD_BUFFER) {
        if (posix_memalign((void**)&THREAD_BUFFER, PAGE_SIZE, SEQUENTIAL_BLOCK_SIZE) != 0) {
            cerr << "线程缓冲区分配失败" << endl;
            exit(1);
        }
    }
    memset(THREAD_BUFFER, '0', SEQUENTIAL_BLOCK_SIZE);
}

bool directio_open_read(string filename, int& fd) {
    // 使用 direct I/O 打开文件用于读取
    fd = open(filename.c_str(), O_RDONLY | O_DIRECT);
    if (fd == -1) {
        cerr << "directio_open_read 打开文件失败: " << strerror(errno) << endl;
        return false;
    }
    return true;
}

bool directio_open_write(string filename, int& fd) {
    // 使用 direct I/O 打开文件用于写入，不存在返回false
    fd = open(filename.c_str(), O_WRONLY | O_DIRECT);
    if (fd == -1) {
        cerr << "directio_open_write 打开文件失败: " << strerror(errno) << endl;
        return false;
    }
    return true;
}

bool directio_open_create(string filename, int write_size_gb) {
    // 使用 direct I/O 打开文件用于写入, 如果存在就清空
    // 并写入 write_size_gb 大小的文件
    int fd = open(filename.c_str(), O_WRONLY | O_DIRECT | O_CREAT | O_TRUNC, 0644);
    if (fd == -1) {
        cerr << "directio_open_create 打开文件失败: " << strerror(errno) << endl;
        return false;
    }
    uint64_t write_size = 1UL * 16 * 1024 * 1024; // 16M
    char* buffer;
    if (posix_memalign((void**)&buffer, PAGE_SIZE, write_size) != 0) {
        cerr << "directio_open_create 分配对齐内存失败" << endl;
        close(fd);
        return false;
    }
    memset(buffer, 0, write_size);
    int extra_write_block = (SEQUENTIAL_BLOCK_SIZE + write_size - 1) / write_size;
    for (int i = 0; i < write_size_gb * 64 + extra_write_block; i++) {
        uint64_t result = write(fd, buffer, write_size);
        if (result != (uint64_t)write_size) {
            cerr << "directio_open_create 写入文件失败: " << strerror(errno) << ", 第" << i + 1 << " 次写入" << endl;
            free(buffer);
            close(fd);
            return false;
        }
    }
    free(buffer);
    close(fd);
    return true;
}

bool read_4k(int fd, uint64_t offset, char* buffer) {
    // 使用 direct I/O 读取 4KB 数据
    if (lseek(fd, offset, SEEK_SET) == -1) {
        cerr << "read_4k 定位失败: " << strerror(errno) << endl;
        return false;
    }
    uint64_t result = read(fd, buffer, PAGE_SIZE);
    if (result != PAGE_SIZE) {
        cerr << "read_4k 读取文件失败: " << strerror(errno) << endl;
        return false;
    }
    return true;
}

bool read_4m(int fd, uint64_t offset, char* buffer) {
    // 使用 direct I/O 读取 4MB 数据
    if (lseek(fd, offset, SEEK_SET) == -1) {
        cerr << "read_4m 定位失败: " << strerror(errno) << endl;
        return false;
    }
    uint64_t result = read(fd, buffer, SEQUENTIAL_BLOCK_SIZE);
    if (result != SEQUENTIAL_BLOCK_SIZE) {
        cerr << "read_4m 读取文件失败: " << strerror(errno) << endl;
        return false;
    }
    return true;
}

bool write_4k(int fd, uint64_t offset, char* buffer) {
    // 使用 direct I/O 写入 4KB 数据
    if (lseek(fd, offset, SEEK_SET) == -1) {
        cerr << "write_4k 定位失败: " << strerror(errno) << endl;
        return false;
    }
    uint64_t result = write(fd, buffer, PAGE_SIZE);
    if (result != PAGE_SIZE) {
        cerr << "write_4k 写入文件失败: " << strerror(errno) << endl;
        return false;
    }
    return true;
}

bool write_4m(int fd, uint64_t offset, char* buffer) {
    // 使用 direct I/O 写入 4MB 数据
    if (lseek(fd, offset, SEEK_SET) == -1) {
        cerr << "write_4m 定位失败: " << strerror(errno) << endl;
        return false;
    }
    uint64_t result = write(fd, buffer, SEQUENTIAL_BLOCK_SIZE);
    if (result != SEQUENTIAL_BLOCK_SIZE) {
        cerr << "write_4m 写入文件失败: " << strerror(errno) << endl;
        return false;
    }
    return true;
}

uint64_t ns_time() {
    return chrono::duration_cast<chrono::nanoseconds>(chrono::high_resolution_clock::now().time_since_epoch()).count();
}

bool thread_worker(const atomic<bool>* stop, vector<uint64_t>* results, int id, decltype(&read_4k) func, decltype(&directio_open_read) open_func) {
    // 定义随机数生成器，使用时间和 id 初始化
    std::mt19937_64 rng(ns_time() % 100000000 + id * 1000000000L);
    uint64_t random_max = (1ULL * ARENA_SIZE_GB * 1024 * 1024 * 1024) / PAGE_SIZE - 1;
    std::uniform_int_distribution<uint64_t> dist(0, random_max - 1);
    init_thread_buffer();
    int fd;
    assert(open_func(FILE_NAME, fd) && "thread_worker 打开文件失败");
    int local_count = 0;
    while (true) {
        uint64_t offset = (dist(rng)) * PAGE_SIZE;
        assert(func(fd, offset, THREAD_BUFFER) && "thread_worker 读写文件失败");
        if (stop->load()) {
            (*results)[id] = local_count;
            return true;
        }
        local_count++;
    }
}

double do_speed_test(int thread_num, double time_sec, bool is_write, bool is_squential) {
    string thread_num_str = (thread_num == 1) ? "单" : (to_string(thread_num) + " ");
    string rw_str = is_write ? "写入" : "读取";
    string seq_random_str = is_squential ? "顺序" : " 4k 随机";
    uint64_t block_size = is_squential ? SEQUENTIAL_BLOCK_SIZE : PAGE_SIZE;
    string test_name = thread_num_str + "线程" + seq_random_str + rw_str;
    cout << test_name << " 开始:" << endl;
    decltype(&read_4k) func;
    decltype(&directio_open_read) open_func;

    if (is_write) {
        func = is_squential ? write_4m : write_4k;
        open_func = directio_open_write;
    } else {
        func = is_squential ? read_4m : read_4k;
        open_func = directio_open_read;
    }

    atomic<bool> stop = false;
    vector<thread> threads;
    vector<uint64_t> results(thread_num, 0);

    uint64_t start_time = ns_time();

    for (int i = 0; i < thread_num; i++) {
        threads.emplace_back(thread_worker, &stop, &results, i, func, open_func);
    }

    usleep(round(time_sec * 1000000));
    stop.store(true);
    double actual_time = (double)(ns_time() - start_time) / 1000000000;

    for (auto& t : threads) {
        t.join();
    }

    uint64_t total_io_count = 0;
    for (uint64_t x : results) {
        total_io_count += x;
    }
    double total_bytes = total_io_count * block_size;
    double mb_per_sec = total_bytes / actual_time / (1024 * 1024);
    cout << "    结果: " << mb_per_sec << " MB/s" << endl;
    cout << "    IO 次数: " << total_io_count << ", 单块大小: " << block_size << endl << endl;
    return mb_per_sec;
}

int main(int argc, char* argv[]) {
    if (argc == 1) {
        cerr << "文件名未提供" << endl;
        return 1;
    }
    FILE_NAME = argv[1];
    ARENA_SIZE_GB = (argc >= 3 && atoi(argv[2]) != 0) ? atoi(argv[2]) : 16;
    TEST_TIME_SEC = (argc >= 4 && atof(argv[3]) != 0) ? atof(argv[3]) : 5.0;
    SEQUENTIAL_READ_THREADS = (argc >= 5 && atoi(argv[4]) != 0) ? atoi(argv[4]) : 4;
    RANDOM_READ_THREADS = (argc >= 6 && atoi(argv[5]) != 0) ? atoi(argv[5]) : 64;
    SEQUENTIAL_WRITE_THREADS = (argc >= 7 && atoi(argv[6]) != 0) ? atoi(argv[6]) : 4;
    RANDOM_WRITE_THREADS = (argc >= 8 && atoi(argv[7]) != 0) ? atoi(argv[7]) : 64;
    cout << "文件名: " << FILE_NAME << endl;
    cout << "Arena 大小 (GB): " << ARENA_SIZE_GB << endl;
    cout << "顺序读线程数: " << SEQUENTIAL_READ_THREADS << endl;
    cout << "随机读线程数: " << RANDOM_READ_THREADS << endl;
    cout << "顺序写线程数: " << SEQUENTIAL_WRITE_THREADS << endl;
    cout << "随机写线程数: " << RANDOM_WRITE_THREADS << endl;
    cout << "测试时间 (秒): " << TEST_TIME_SEC << endl;
    cout << endl;

    cout << "正在创建测试文件 ..." << endl;
    assert(directio_open_create(FILE_NAME, ARENA_SIZE_GB) && "创建测试文件失败");
    cout << "创建测试文件完成" << endl;
    
    do_speed_test(1, TEST_TIME_SEC, false, true); // 单线程顺序读取
    do_speed_test(SEQUENTIAL_READ_THREADS, TEST_TIME_SEC, false, true); // 4 线程顺序读取
    do_speed_test(1, TEST_TIME_SEC, false, false); // 单线程随机读取
    do_speed_test(RANDOM_READ_THREADS, TEST_TIME_SEC, false, false); // 64 线程随机读取
    do_speed_test(1, TEST_TIME_SEC, true, true); // 单线程顺序写入
    do_speed_test(SEQUENTIAL_WRITE_THREADS, TEST_TIME_SEC, true, true); // 4 线程顺序写入
    do_speed_test(1, TEST_TIME_SEC, true, false); // 单线程随机写入
    do_speed_test(RANDOM_WRITE_THREADS, TEST_TIME_SEC, true, false); // 64 线程随机写入
}

// g++ disk_test.cpp -o disk_test -O3 -pthread
// ./disk_test test.bin 4 0.5
