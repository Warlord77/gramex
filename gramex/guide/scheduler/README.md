title: Schedule tasks

The `schedule:` section in [gramex.yaml](gramex.yaml) lets you run tasks on startup or at specific times. Here is an example:

<iframe src="gramex.yaml"></iframe>

Each named schedule section has the following keys:

- `function`: the function to run (<strong>required</strong>)</li>
- `kwargs`: the keyword arguments to pass to the function. The function will be called as `function(**kwargs)`. These are optional -- the function will by default be called as `function()`.</li>
- `startup`: set this to true to run the function once at startup.</li>

In addition, the schedule is specified via the `minutes`, `hours`, `dates`, `weekdays`, `months` and `years` keys.

- Any of these 6 fields may be an asterisk (*). This would mean the entire range of possible values, i.e. each minute, each hour, etc.</li>
- Any field may contain a list of values separated by commas, (e.g. `1,3,7`) or a range of values (e.g. `1-5`).</li>
- After an asterisk (*) or a range of values, you can use slash `/` to specify that values are repeated periodically. For example, you can write `0-23/2` in `hours:` to indicate every two hours (it will have the same effect as `0,2,4,6,8,10,12,14,16,18,20,22`); value `*/4` in `minutes:` means that the action should be performed every 4 minutes, `1-10/3` means the same as `1,4,7,10`.</li>
- In `months:` and `weekdays:`, you can use names of months or days of weeks abbreviated to first three letters ("Jan,Feb,...,Dec" or "Mon,Tue,...,Sun") instead of their numeric values. Case does not matter.</li>

For example, this configuration runs at on the 15th and 45th minute every 4 hours on the first and last day of the month (if it's a weekday) in 2016-17.

    run-when-i-say:
        function: schedule_utils.log_time
        minutes: '15, 45'           # Every 15th & 45th minute
        hours: '*/4'                # Every 4 hours
        dates: '1, L'               # On the first and last days of the month
        weekdays: 'mon-fri'         # On weekdays
        months: '*'                 # In every month
        years: '2016, 2017'         # the next 2 years