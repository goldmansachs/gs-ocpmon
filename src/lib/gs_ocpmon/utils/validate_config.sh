#!/bin/sh

if [[ $# -ne 1 ]]; then
	echo "Mandatory Argument Missing"
	echo $0 "<config-file>/<config-directory>"
	exit 0
fi

config_file="$1"
if [[ -f "${config_file}" ]];then
	python -m json.tool "${config_file}"
	ret=$?
	if [[ $ret -ne 0 ]];then
		echo "${config_file}" " : Not a Valid Config File" 	
		exit 1
	fi
	
elif  [[ -d "${config_file}" ]];then
	for f in $(find "${config_file}" -name '*.json'); do 
		python -m json.tool $f
		ret=$?
	        if [[ $ret -ne 0 ]];then
                	echo $f " : Not a Valid Config File"
        	fi

	done
	
else
	echo "Input Provided is not a File/Directory"
	exit 1
fi
