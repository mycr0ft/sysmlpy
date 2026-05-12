// XPECT noErrors ---> ""
package P {
    part def Vehicle {
        public import ScalarValues::*;
        attribute a: Integer = 5;
        attribute b: Integer = 5 * a;
    }
}
