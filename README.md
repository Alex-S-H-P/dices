# Dices


A ClI-based calculator with dice rolling in mind.

## Table of contents

* [Table of contents](#table-of-contents)
* [General explaination](#general-explanation)
* [Specifics](#specifics)
  * [Advantage](#advantage)
  * [Criticals](#criticals)
  * [Dropping dice](#dropping)
  * [Comparisons](#comparisons)
  * [Graphing](#graphing)
* [Dice bot](#dice-bot)

## General explanation

Use the `dices` command to launch the parser.

You will then be presented with this prompt.

```
------------------------------------------
DICE ENVIRONMENT
------------------------------------------

>>> 
```

You can then input a command. Each command will simply be a formula like `1 + 2 + 3`.
DICES will then parse through this prompt and execute it.

What sets this apart here is the ability to use dice commands instead of values.
So on top of `1 + 2 + 3`, you can use `1d2 + 1d4`.

Please note that the expected value and the maximal values are returned on each computation, whether it contains dice commands or not.
It might look like this :
```	Result :

Got 3 (out of 6 maximum, 4.0 expected)
```

Dice operators are composed of two numbers separated by a "d".
	* the leftmost number is the number of dice to be rolled. When absent, it is defaulted to 1.
	* the rightmost number is the number of sides to the die.

## Specifics

There are a lot more commands than just simple maths with dice.
The abilities have grown corresponding to my own needs in table-top RPGs.

DICES is not case sensitive.

#### Exiting

When your game is over, you may be tempted to just close the terminal window, but you don't need to.

Either imputing a blank command or a `quit` will tell DICES that you want to leave, now.

#### Equivalences

`quit` is equivalent to :

* `q`
* `no`
* `bye`
* `exit`
* `e`
* `-q`
* `-e`

### Advantage

You can also use the `adv` and the `disadv` key-words to enable advantage and disadvantage.

### Criticals

You can now have a dnd compatible set of dices thanks to the handy `dnd` keyword.

You will now be warned if any of the d20s reach a critical value !

#### More control.

The `reset` single line command allows to erase all critical dices. 

You can deem that dices other than D20s are critical, 
and therefore expect those to tell you if they reach critical values (their minimum or their maximum).

To do so, you can use **pre-command instructions**.
Those are executed, not on the execution step, but in compilation at the token seperation stage.

These instructions are to be placed at the beginning of the command, and are to use seperators to mark their limit.

These token can be :

* "|", which is the default separating token
* "#", which is its alternative
* "&", which denotes that the result of the operation should be permanent.

**NB** : Old documentation may mention the use of ">". 
As of the comparison update, this token can no longer be used as a seperator.

The instruction "crit" can then be used. 
It requires its argument to be a die, declared as "dN", where N is the value of the die.


#### Example
The dnd shortcut can be used like this :
```
>>> dnd
>>> 1d20
```
But it is a shortcut, as you could simply write
```
>>> crit d20 & d20
```
Or, if you wanted those results to be announced just once :
```
>>> crit d20 | d20
```
And finally to erase all critical dice :
```
>>> reset
```

#### Equivalences :

These tokens are equivalent :

* for `dnd`:
  * `d&d`
  * `critical`
  * `crit`
  * `dungeon&dragon`
  * `crits`
  * `criticals`
  * `dungeon & dragon`
  * `dungeon and dragon`
  * `count crits`
  * `count criticals`
  * `count critical`
  * `d&d&d&d`
* for `crit` (when used as a pre-command instruction):
  * `crits`
  * `crit`
  * `warn`
  * `warns`
  * `critical`
  * `c`
  * `-c`
* for `reset`:
  * `reboot`
  * `rb`
  * `boot`
  * `nocrit`

### Dropping

You can drop die depending on their result.

This allows to roll "4d6 drop lowest" by litterally typing `4d6 drop lowest`.

To drop multiple dice, just add this number to the command argument.

To drop two dices, you can just say :

`>>> 4d6 drop lowest2`

### Comparisons

You can now afford to compare dices and values !

To do so, simply use the comparaison operators ! These are :
	* >  for "greater than"
	* <  for "lesser than"
	* <= for "lesser or equal"
	* >= for "greater or equal"
	* =  for "equal"
	* != for "not equal"


#### Example :

These operators return the number of successful comparisons. Here are a few examples : 

```
>>> 4d10 > 6
```
This will return the number of dices that got more than 6.

```
>>> d20 > 14
```
Returns 1 if the dice rolls over a 14.

```
>>> 2 + 6d20 > 14
```
This will add 2 to the numbers of count of dices that are over 14.

```
>>> 6d20 + 2 > 14
```
This will run the comparison, just find a failed comparison (since 2 < 14), and then add 6d20 over that. 
If you don't want this behavior, just add parentheses !

```
>>> (6d20 + 2) > 14
```
Which will compute 6d20 + 2 and compare that to 14.

### Graphing

When rolling a die, one can wonder what the odds of their rolls where. Wonder no further !

Thanks to the `graph` command, you can now see the odd of every result you could have had !

The `graph` is a single line command. It should be the only thing input when it is.
As a command that fetches the previous result, it expects a command to have been executed previously.

#### Example :

When running :

```
>>> d4*2d12
>>> graph
```

You can expect this kind of result :

```
0.10+                 ###
    |               #######
    |              #########
    |            #############
    |          #################
0.00+-----+----+----+----+----+----+----+>   +
     12   17   22   27   32   37   42   47   52
                      ^
```

_In this particular case, a 29 was rolled. This had about 1/10 chances of happening._

#### Equivalences : 

These commands are equivalent to `graph` :
* `draw`
* `g`
* `repartition`
* `see`

## Dice bot

We also add a set of utilities to the `dices` toolkit for discord integration.

### How to deploy the bot

We recommend you follow a tutorial such as the one at [select hub](https://www.selecthub.com/resources/how-to-add-bots-to-discord/) to get your token.

Save your token as the file `key.key` in the src folder (this file is ignored by git. If you copy this repository on any other VCS, ensure that the token is not copied along).

You can then use `python3.10 src/main.py` to launch the bot.

### Command line arguments

The dices-bot has a few extra abilities. Their usage is usually as such : `routine [arguments...]`.
Here are a few examples :

- The **say** routine:
  - will print on launch of the bot to any `test-bots` channel its one argument
- The **to** routine:
  - will redirect the previous say routine to any default channel of a given server or any channel of this name of any server the bot is connected to. 
  - has one argument, the name of the channel/server