#!/usr/bin/env bash

set -o errexit
set -o pipefail

debug=false
for arg in "$@"; do
    if [ "$arg" == "debug" ]; then
        debug=true
    fi
done

server_state_cmd="rippled --silent server_state"
server_state=$($server_state_cmd | tail -n+4) # tail -n+4 to deal with voidstar output

if $debug; then
    echo $server_state
fi

state_regex='"server_state" : "(\w+)"'

complete_ledgers_regex='"complete_ledgers" : "([[:digit:]]+-[[:digit:]]+)"' # BUG: will break on gaps
state_file="/sync.state"

if [[ $server_state =~ $state_regex ]]; then
    state="${BASH_REMATCH[1]}"
fi

if [[ $server_state =~ $complete_ledgers_regex ]]; then
    complete_ledgers="not_empty"
    # echo ${BASH_REMATCH[1]}do
fi

if [[ "${HOSTNAME}" =~ ^val[[:digit:]]$ ]]; then
    ready_state="proposing"
elif [[ "${HOSTNAME}" =~ ^rippled$ ]]; then
    ready_state="full"
fi

if [[ "${state}" = "${ready_state}" && "${complete_ledgers}" = "not_empty" ]]; then
    if [ ! -f $state_file  ]; then
        uptime=$($server_state_cmd | grep -oP '"uptime"\s*:\s*\K\d+')
        echo "synced" > $state_file
        echo "synced after $uptime seconeds" > "synctime"
    fi
    state="ready"
else
    state="not ready"
fi

if $debug; then
    echo "rippled $state"
fi

if [ "$state" = "ready" ]; then
    echo "$HOSTNAME ready after $uptime seconds."
    exit 0
fi
exit 1
