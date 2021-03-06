#!/bin/bash

# get directory of script
DIR="$( cd "$( dirname "$0" )" && pwd )"

#LOCAL_GUACAMOLE="$DIR/../../../guacamole"
#LOCAL_AVANGO="$DIR/../../../avango"

# if not, this path will be used
GUACAMOLE=/home/wabi7015/Programming/guacamole
AVANGO=/home/wabi7015/Programming/avango

# third party libs
export LD_LIBRARY_PATH=/opt/boost/current/lib:/opt/zmq/current/lib

# schism
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/schism/current/lib/linux_x86

# avango
export LD_LIBRARY_PATH="$AVANGO/lib":$AVANGO/lib:$LD_LIBRARY_PATH:/opt/lamure/install/lib:/opt/Awesomium/lib
export PYTHONPATH="$AVANGO/lib/python3.4":"$AVANGO/examples":$AVANGO/lib/python3.4:$AVANGO/examples

# guacamole
export LD_LIBRARY_PATH="$GUACAMOLE/lib":$GUACAMOLE/lib:$LD_LIBRARY_PATH

# run daemon
if [ -f "$LOCAL_AVANGO/examples/examples_common/daemon.py" ]
then
    python3 $LOCAL_AVANGO/examples/examples_common/daemon.py > /dev/null &
else
    python3 $AVANGO/examples/examples_common/daemon.py > /dev/null &
fi

# run program
if [[ $* == *-d* ]]
then
cd "$DIR" && gdb --args python3.4 ./main.py
else
cd "$DIR" && python3.4 ./main.py
fi

# kill daemon
kill %1
