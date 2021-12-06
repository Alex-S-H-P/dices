# Dices
a dice-parser to allow for better dnd games


use the `dices` command to launch the parser.

You will then be presented with this prompt.

```
------------------------------------------
DICE ENVIRONMENT
------------------------------------------

```

You can then input a command. Each command will just be a formula like `1 + 2 + 3`
It will then parse the formula, and return its value.

What is important here is that you can use dice commands instead of values.
So instead of `1 + 2 + 3`, you can use `1d2 + 1d4`.

Please note that the expected value and the maximal values are returned on each computation, whether it contains dice commands or not.
It might look like this :
```	Result :

Got 3 (out of 6 maximum, 4.0 expected)
```

You can also use the `adv` and the `disadv` key words to enable advantage and disadvantage. **Please note that as of yet, critical success or failure is not taken into account when considering this**

## UPDATE RELEASE 2

You can now have a dnd compatible set of dices thanks to the handy `dnd` keyword.

You can use it like this !
```
dnd
1d20
```

You will now be warned if any of the d20s reach a critical value !

have fun !
