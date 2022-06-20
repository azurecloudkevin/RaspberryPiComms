#!/bin/bash
# /usr/sbin/change_hostname.sh - program to permanently change the hostname
# Permissions are set so that www-user can do sudo for this specific program

# args:
# $1 - new hostname, should be a legal hostname

sed -i "s/$HOSTNAME/$1/g" /etc/hosts
echo $1 > /etc/hostname
hostname $1 # to complete hostname change without restarting