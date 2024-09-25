#include <chrono>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <mutex>
#include <thread>
#include <vector>
#include <random>
#include <unistd.h>

using namespace std;
using namespace std::chrono;

const double SINGLE_TEST_SIZE = 2;  // GB
const double MULTIPLE_TEST_SIZE = 4;  // GB
const int TIMES = 10;
const uint64_t SEGMENT_SIZE = 1024 * 1024 * 1; // 1 MB
const uint64_t AREA_SIZE = 4UL * 1024UL * 1024UL * 1024UL; // 4 GB

struct segment {
    char _[1024*1024];
};

double write_single(void* area) {
    uint64_t test_size = SINGLE_TEST_SIZE * 1024UL * 1024UL * 1024UL;
    uint64_t times = test_size / SEGMENT_SIZE;
    uint64_t range_end = AREA_SIZE - SEGMENT_SIZE;
    std::random_device rd;
    std::mt19937_64 eng(rd());
    std::uniform_int_distribution<uint64_t> distr(0, range_end);
    auto start = high_resolution_clock::now();
    for (int i=0; i<times; i++){
        uint64_t r = distr(eng);
        uint8_t r2 = distr(eng);
        memset((char*)area + r, r2, SEGMENT_SIZE);
    }
    auto end = high_resolution_clock::now();
    auto duration = duration_cast<milliseconds>(end - start).count();
    return SINGLE_TEST_SIZE / ((double)duration / 1000);
}

void write_64_worker(int64_t* times, mutex* mtx, void* area, int seed) {
    std::mt19937_64 eng(seed);
    std::uniform_int_distribution<uint64_t> distr(0, AREA_SIZE - SEGMENT_SIZE);
    while (true) {
        {
            lock_guard<mutex> lock(*mtx);
            if (*times <= 0) {
                return;
            }
            (*times)--;
        }
        uint64_t r = distr(eng);
        uint8_t r2 = distr(eng);
        memset((char*)area + r, r2, SEGMENT_SIZE);
    }
}

double write_64(void* area) {
    uint64_t test_size = MULTIPLE_TEST_SIZE * 1024UL * 1024UL * 1024UL;
    int64_t times = test_size / SEGMENT_SIZE;
    mutex mtx;
    std::random_device rd;
    int tmp = rd();
    vector<thread> threads;
    auto start = high_resolution_clock::now();
    for (int i = 0; i < 64; i++) {
        thread t(write_64_worker, &times, &mtx, area, i+tmp);
        threads.push_back(move(t));
    }
    for (int i = 0; i < 64; i++) {
        threads[i].join();
    }
    auto end = high_resolution_clock::now();
    auto duration = duration_cast<milliseconds>(end - start).count();
    return MULTIPLE_TEST_SIZE / ((double)duration / 1000);
}

double read_single(void* area) {
    uint64_t test_size = SINGLE_TEST_SIZE * 1024UL * 1024UL * 1024UL;
    uint64_t times = test_size / SEGMENT_SIZE;
    uint64_t range_end = AREA_SIZE - SEGMENT_SIZE;
    std::random_device rd;
    std::mt19937_64 eng(rd());
    std::uniform_int_distribution<uint64_t> distr(0, range_end);
    volatile uint64_t sum = 0;
    auto start = high_resolution_clock::now();
    for (int i=0; i<times; i++){
        uint64_t r = distr(eng);
        uint64_t tt = SEGMENT_SIZE/8;
        uint64_t* area2 = (uint64_t*)((char*)area+r);
        uint64_t sum2 = 0;
        for (int j=0; j<tt; j++){
            sum2 |= area2[j];
        }
        sum += sum2;
    }
    auto end = high_resolution_clock::now();
    auto duration = duration_cast<milliseconds>(end - start).count();
    return SINGLE_TEST_SIZE / ((double)duration / 1000);
}

void read_64_worker(int64_t* times, mutex* mtx, void* area, int seed) {
    std::mt19937_64 eng(seed);
    std::uniform_int_distribution<uint64_t> distr(0, AREA_SIZE - SEGMENT_SIZE);
    volatile uint64_t sum = 0;
    while (true) {
        {
            lock_guard<mutex> lock(*mtx);
            if (*times <= 0) {
                return;
            }
            (*times)--;
        }
        uint64_t r = distr(eng);
        uint64_t tt = SEGMENT_SIZE/8;
        uint64_t* area2 = (uint64_t*)((char*)area+r);
        uint64_t sum2 = 0;
        for (int j=0; j<tt; j++){
            sum2 |= area2[j];
        }
        sum += sum2;
    }
}

double read_64(void* area) {
    uint64_t test_size = MULTIPLE_TEST_SIZE * 1024UL * 1024UL * 1024UL;
    int64_t times = test_size / SEGMENT_SIZE;
    mutex mtx;
    std::random_device rd;
    int tmp = rd();
    vector<thread> threads;
    auto start = high_resolution_clock::now();
    for (int i = 0; i < 64; i++) {
        thread t(read_64_worker, &times, &mtx, area, i+tmp);
        threads.push_back(move(t));
    }
    for (int i = 0; i < 64; i++) {
        threads[i].join();
    }
    auto end = high_resolution_clock::now();
    auto duration = duration_cast<milliseconds>(end - start).count();
    return MULTIPLE_TEST_SIZE / ((double)duration / 1000);
}

void test() {
    // to ensure cpu speed is not the bottleneck
    void* area3 = malloc(SEGMENT_SIZE);
    memset(area3, rand() % 256, SEGMENT_SIZE);
    memset(area3, rand() % 256, SEGMENT_SIZE);
    volatile uint64_t this_sum = 0;
    uint64_t* area4 = (uint64_t*)area3;
    // here is to forcely put it into cache
    for (int i=0; i<1000; i++){
        uint64_t this_sum2 = 0;
        uint64_t tt = SEGMENT_SIZE/8;
        for (int j=0; j<tt; j++){
            this_sum2 |= area4[j];
        }
        this_sum += this_sum2;
    }
    auto start = high_resolution_clock::now();
    // this will not be optimized by compiler, because change from 100 to 1000, the time actually increases
    for (int i=0; i<1000; i++){
        uint64_t this_sum2 = 0;
        uint64_t tt = SEGMENT_SIZE/8;
        for (int j=0; j<tt; j++){
            this_sum2 |= area4[j];
        }
        this_sum += this_sum2;
    }
    auto end = high_resolution_clock::now();
    auto duration = duration_cast<milliseconds>(end - start).count();
    cout << duration << endl;
}

int main() {
    // test();
    // sleep(10000);
    srand(time(NULL));
    void* area = malloc(AREA_SIZE); // 4 GB
    memset(area, rand() % 256, AREA_SIZE);
    memset(area, rand() % 256, AREA_SIZE);

    double single_write = 0;
    cout << "Single thread writing:" << endl;
    write_single(area);  // warm up
    for (int i = 0; i < TIMES; i++) {
        double s = write_single(area);
        single_write += s;
        cout << i + 1 << ". " << s << " GB/s" << endl;
    }
    cout << "Average: " << single_write / TIMES << " GB/s" << endl
         << endl;

    double multiple_write = 0;
    cout << "64 threads writing:" << endl;
    write_64(area);  // warm up
    for (int i = 0; i < TIMES; i++) {
        double s = write_64(area);
        multiple_write += s;
        cout << i + 1 << ". " << s << " GB/s" << endl;
    }
    cout << "Average: " << multiple_write / TIMES << " GB/s" << endl
         << endl;

    double single_read = 0;
    cout << "Single thread reading:" << endl;
    read_single(area);  // warm up
    for (int i = 0; i < TIMES; i++) {
        double s = read_single(area);
        single_read += s;
        cout << i + 1 << ". " << s << " GB/s" << endl;
    }
    cout << "Average: " << single_read / TIMES << " GB/s" << endl
         << endl;

    double multiple_read = 0;
    cout << "64 threads reading:" << endl;
    read_64(area);  // warm up
    for (int i = 0; i < TIMES; i++) {
        double s = read_64(area);
        multiple_read += s;
        cout << i + 1 << ". " << s << " GB/s" << endl;
    }
    cout << "Average: " << multiple_read / TIMES << " GB/s" << endl
         << endl;

    free(area);
    return 0;
}


// Compile command:
// g++ test.cpp -O3 -w
// If this fails, use the following:
// g++ test.cpp -O3 -w -pthread
