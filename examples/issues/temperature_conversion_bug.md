# Bug: Celsius conversion subtracts instead of adding offset

`celsius_to_fahrenheit(0)` should be `32`, and `celsius_to_fahrenheit(100)` should be `212`.
The current conversion uses the wrong sign for the Fahrenheit offset.
