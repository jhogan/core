lines=$(grep 'class.*tester)' *.py)


echo "$lines" | while read l; do 
    f=`echo $l | awk -F: '{print $1}'`
    c=`echo $l | sed 's/^.*class \([a-z_]\+\).*/\1/'`

    echo "$f $c" | while read l; do 
        python3 $l;
    done
done

