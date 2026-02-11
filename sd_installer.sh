#!/usr/bin/sh
# 
# setup script to copy the local ./setup directory to
# /usr/local/setup on the SD card
# then run some customization
#
######################################################
usage() {
	echo "Usage: $this -p 'SD card mount point' -t 'target directory on SD card' [ -s optional ssh key ]"  1>&2
	[ "$usage_errors" ] && echo "$usage_errors"
	exit 1
}

this=$(basename "$0")
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
echo "SCRIPT_DIR is [$SCRIPT_DIR]"

# optional: ssh key
local_ssh_key=
path_errors=''
usage_errors=''
while getopts ":p:t:s:" o; do
	case "${o}" in
		p) rootdir=${OPTARG}
			c1=$(echo $rootdir | cut -c1)
			if [ "$c1" = "-" ]  ; then
			  	path_errors="${path_errors}SD card mount point is required\n"
			elif [ ! "$c1" = "/" ] ; then
				path_errors="${path_errors}[$rootdir] is not a valid path\n"
			else
				[ -d "$rootdir" ] || { path_errors="${path_errors}SD card mount point [$rootdir] does not exist\n" ; }
			fi
			;;
		t) topdir=${OPTARG}
			c1=$(echo $topdir | cut -c1)
			if [ "$c1" = "-" ]  ; then
				path_errors="${path_errors}SD card target dir is required\n"
			elif [ ! "$c1" = "/" ] ; then
				path_errors="${path_errors}[$topdir] is not a valid path\n"
			fi
			# if [ -d "$rootdir" ] ; then
			#	[ -d "$rootdir/$topdir" ] || { usage_errors="${usage_errors}[$topdir] not found on SD card\n" ; }
			# fi
			;;
		s) local_ssh_key=${OPTARG}
			[ -f "$local_ssh_key" ] || { usage_errors="${usage_errors}ssh key file [$local_ssh_key] not found\n" ; }
			;;
		*) usage
			;;
	esac
done
shift $((OPTIND-1))
echo "rootdir [$rootdir]"
echo "topdir [$topdir]"
echo "local_ssh_key [$local_ssh_key]"
[ -z "$rootdir" ] || [ -z "$topdir" ] && usage
if [ -z "$path_errors" ] ; then 
	if [ ! -d "$rootdir$topdir" ] ; then
		upper_dir=$(dirname $rootdir$topdir)
		if [ ! -d "$upper_dir" ] ; then
			usage_errors="${usage_errors}[$upper_dir] not found on SD card\n"
		fi
		# usage_errors="${usage_errors}[$topdir] not found on SD card\n"
	fi
else
	usage_errors=${usage_errors}${path_errors}
fi
[ "$usage_errors" ] && usage

if [ -d $SCRIPT_DIR/setup ] ; then
	:
else
	echo "$this: expected to find setup directory in $SCRIPT_DIR"
	echo "Please check and resolve"
	exit 1
fi

# create local directories
for dir in data microdot
do
	if [ -d $SCRIPT_DIR/setup/$dir ] ; then
		:
	else
		mkdir $SCRIPT_DIR/setup/$dir
		# mkdir should provide a suitable error message
		[ $? -eq 0 ] || exit 1
	fi
done
# create local subdirectories
for subd in templates lists 
do
	if [ -d $SCRIPT_DIR/setup/hotspot/$subd ] ; then
		:
	else
		mkdir -p $SCRIPT_DIR/setup/hotspot/$subd
		# mkdir should provide a suitable error message
		[ $? -eq 0 ] || exit 1
	fi
done
# set up local symlinks for microdot
for dir in application hotspot
do
	if [ -L $SCRIPT_DIR/setup/$dir/microdot ] ; then
		:
	else
		cd $SCRIPT_DIR/setup/$dir/ && ln -s ../microdot .
	fi
done

# change the _TARGET_ in systemd/cust-net.service
sed -s "s|_TARGET_|$topdir|g" ./setup/systemd/cust-net.template > ./setup/systemd/cust-net.service

mkdir $rootdir$topdir
cp -r $SCRIPT_DIR/setup/* $rootdir$topdir
ksh -x ./local_setup $rootdir $topdir $local_ssh_key
