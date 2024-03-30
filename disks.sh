#!/bin/bash


# 输入密码
echo "请输入LUKS加密分区的密码："
read -s luks_password

# 未加密的
declare -a labels=("TMP" "SWAP")
base_mount_point="/media/jtc"

while IFS= read -r line; do
    # 从blkid输出中分离设备文件和标签
    device=$(echo $line | awk '{print $1}')
    label=$(echo $line | grep -oP 'LABEL="\K[^"]+')
    device="${device%?}"  # 删除设备文件名中的冒号
    if [[ " ${labels[@]} " =~ " ${label} " ]]; then
        echo "Device: $device, Label: $label"
        mount_point="${base_mount_point}/${label}"
        mkdir -p "$mount_point"
        echo "挂载分区：$device -> $mount_point"
        if mount -t ext4 "$device" "$mount_point"; then
            echo "$device 已成功挂载到 $mount_point"
        else
            echo "无法挂载 $device 到 $mount_point"
        fi
    fi
    echo ""
done < <(blkid)

# 加密分区
luks_devices=$(blkid | grep 'TYPE="crypto_LUKS"' | awk '{print $1}' | sed 's/://')
for device in $luks_devices; do
    echo "发现LUKS加密分区：$device"
    decrypted_name="decrypted_$(basename $device)"
    printf "%s" "$luks_password" | cryptsetup luksOpen $device $decrypted_name --key-file=-
    if [ $? -eq 0 ]; then
        echo "$device 解锁成功，映射为：/dev/mapper/$decrypted_name"
        eval $(sudo blkid -o export /dev/mapper/$decrypted_name)
        mount_label=${LABEL:-$decrypted_name}
        mount_point="${base_mount_point}/$mount_label"
        sudo mkdir -p "$mount_point"
        echo "挂载分区：/dev/mapper/$decrypted_name -> $mount_point"
        sudo mount /dev/mapper/$decrypted_name $mount_point
        if [ $? -eq 0 ]; then
            echo "/dev/mapper/$decrypted_name 已成功挂载到 $mount_point"
        else
            echo "无法挂载 /dev/mapper/$decrypted_name 到 $mount_point"
        fi
    else
        echo "$device 解锁失败"
    fi
    echo ""
done
