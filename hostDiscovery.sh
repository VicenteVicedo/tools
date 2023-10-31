#!/bin/bash

#añadir -x para examinar una ip: TTL, MAC (vendor...), ...
#cabeceras de servicios con nc

trap SIGINT_handler INT

SIGINT_handler(){
    echo "Exiting..."
    exit 1
}

interfaces=$(ip link show | grep -oP "\d: (.*):" | grep -P ":" | sed 's/[0-9]: //' | sed 's/://')

# Function to split the CIDR notation into IP address and subnet mask
get_ip_range() {
    local cidr="$1"
    IFS='/' read -r -a parts <<< "$cidr"
    local ip="${parts[0]}"
    local mask="${parts[1]}"
    
    local ip_arr
    local network_ip
    local wildcard_mask
    local ip_range_start
    local ip_range_end

    IFS='.' read -r -a ip_arr <<< "$ip"

    # Calculate the subnet mask from the prefix
    mask=$((0xFFFFFFFF << (32 - mask)))

    for i in {0..3}; do
        network_ip[$i]=$((ip_arr[i] & (mask >> (24 - 8 * i)) ))
        wildcard_mask[$i]=$((255 - (mask >> (24 - 8 * i)) & 254))
        ip_range_start[$i]=$((network_ip[i]))
        ip_range_end[$i]=$((network_ip[i] + wildcard_mask[i]))
    done

    for i in $(seq ${ip_range_start[0]} ${ip_range_end[0]}); do
        for j in $(seq ${ip_range_start[1]} ${ip_range_end[1]}); do
            for k in $(seq ${ip_range_start[2]} ${ip_range_end[2]}); do
                for l in $(seq ${ip_range_start[3]} ${ip_range_end[3]}); do
                    printf "%d.%d.%d.%d\n" "$i" "$j" "$k" "$l"
                done
            done
        done
    done
}


discover_ports() {
    start=$fromPort || start=0
    end=$toPort || end=1024
    echo "-----Discovering ($start:$end) ports for $1-----"
    for port in $(seq $start $end); do
        timeout 5 bash -c "echo '' > /dev/tcp/$1/$port" &>/dev/null && echo "[+] Port $port open" &
    done;
    echo "++++++++++++++++++++++++++++++++++"
}

opt_string="r:hic:d:p:f:"
while getopts $opt_string option; do
    case $option in
        r)  IFS=',' read -ra range <<< $OPTARG
            fromPort=${range[0]}
            toPort=${range[1]}
            ;;
    esac
done

OPTIND=1

while getopts $opt_string option; do
    case $option in
        #r) range=$OPTARG
        #    ;;
        h)
            echo -e "-i\t\t\t list interfaces"
            echo -e "-r <0:1024>\t\t set port range scan"
            echo -e "-c <ip/mask>\t\t calc subnet"
            echo -e "-d <interface>\t\t discover network"
            echo -e "-p <ip>\t\t discover ports in ip"
            echo -e "-f <interface>\t\t discover hosts and ports"
            exit;;
        i) # display interfaces
            echo $interfaces
            exit;;
        c) # calc subnet
            get_ip_range $ipMask
            exit;;
        d) #discover network
            ipMask=$(ip -4 addr show $OPTARG | grep -oP '(?<=inet\s)\d+(\.\d+){3}/[0-9]{2}')

            for ip in $(get_ip_range $ipMask); do
                timeout 1 ping -c 1  $ip >/dev/null && echo "[+] $ip - activo" &
            done; wait
            exit;;
        p)
            ip=$OPTARG
            discover_ports $ip
            exit;;
        f)
            ipMask=$(ip -4 addr show $OPTARG | grep -oP '(?<=inet\s)\d+(\.\d+){3}/[0-9]{2}')
            for ip in $(get_ip_range $ipMask); do
                timeout 1 ping -c 1  $ip >/dev/null && discover_ports $ip
            done; wait
            exit;;
        \?) # Invalid option
            echo "Error: Invalid option"
            exit;;
   esac
done
