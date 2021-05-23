tracking_path="/home/jetxeberria/documents/besteak/erosketak/serbitxuak/antenas_navarra/tracking/"
while true
do
  signal=$(ping -c 1 8.8.8.8 2>/dev/null )
#  connection=$(grep -e '1 received' $tracking_path"internet_tracker.txt" -o)
  connection=$( grep -o -e '1 received' <<< $signal )

  ### If the connection request has not been answered...
  if [[ $connection != *1* ]]; then
    echo "Internet signal lost"
    ### Take current time
    date="$(date)"
    time1="$(date +%s)"
    timediff=0
    returned=0
    ### Track again signal until it is read again
    while [[ $returned == 0 ]]
    do
      new_signal=$(ping -c 1 8.8.8.8 2>/dev/null )
      new_connection=$(grep -o -e '1 received' <<< $new_signal)
      if [[ $new_connection == *1* ]]; then
        echo "Internet signal returned"
        returned=1
        timediff="$(($(date +%s)-time1))"
      fi
      sleep 1
    done

    ### Save time in a readable way. Only if it is greater than '10' seconds.
    if [[ $timediff -gt 10 ]]; then
      time_mins=$(($timediff / 60))
      time_secs=$(($timediff - $time_mins*60))
      time_hours=$(($time_mins / 60))
      time_mins=$(($time_mins-$time_hours*60))
      
      error_msg="Failure on $date of ${time_hours} hours ${time_mins} minutes ${time_secs} seconds."
      echo ${error_msg} >> $tracking_path'failure_tracking.txt'

    fi
  fi
  sleep 2
done
