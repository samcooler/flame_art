# lc_test

While `flamatik` originally started out as a test, it outgrew its humble roots.

Therefore we need a program that is simpler and better for testing.

## Mapping servos and calibrating

This program has ended up being a good program to map servos.

Use this process with HSIs on and fire on. Remove all the "hats" and set all the needle valves
to fully open. 

** Validate that you have ignition on all nozzles without the servos in play. **

First, it's efficient to have all the *solenoids* mapped on the sculpture itself.
This was done incorrectly by Brian 10/24 before Decom, using black sharpie. It
is incorrect because the numbers are "off by one" eg Negative indexec. To get the actual
zero indexed face numbers, *add one*. 

Second, using this program, pick a servo (eg, servo 0). Use the following command to cause
it to sweep between 0 and 255.

```
python lc_test.py --solenoid 10 --servo 0 
```

At this point, it doesn't matter what solenoid you choose, because you're just looking for the servo.

Once you find the servo, figure out which solenoid it is attached to, and start using that command. Once you open the correct solenoid, you should be able to validate fire, and you
now know the mapping between a solenoid and a servo. 

You're going to set the value to the "low value" while installing the "hat". You might as well turn the servo to its low position. 

```
python lc_test.py --solenoid 17 --servo 0 --flow 0 --hold
```

You can also set the low range value to something slightly higher than 0, eg, about 30. This enshures there is enough low to close the valve enough - but makes the system in danger of slight jamming.

Now, set the value of the servo to something low. At first, we were using 0, but it might be better to set it a little lower, like so. If you do that, we should probably have the "sweep" feature take a range to avoid burning out servos.

```
python lc_test.py --solenoid 17 --servo 0 --flow 50 --hold
```

Assemble the servo by setting the needle valve to closed, and either put the small plastic horn on the servo or on the needle valve, and carefully reassemble.

Now test with a 0 to 255 range.

```
python lc_test.py --solenoid 17 --servo 0
```

Validate the range "looks good" and redo if necessary.

Write down the solenoid and servo mapping, because you will need to update the flamatik map.