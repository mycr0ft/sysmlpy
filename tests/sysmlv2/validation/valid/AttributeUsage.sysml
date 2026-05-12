// XPECT noErrors ---> ""
package 'Blocks Example' {
	public import ScalarValues::*;
	
	part def Vehicle {
		attribute status : VehicleStatus;
		attribute b : Boolean;
		attribute s : String;
		attribute p: Positive;
		attribute n: Natural;
		attribute r: Rational;
		attribute re: Real;	
		attribute c: Complex;
	}
	
	attribute def VehicleStatus {
		gearSetting : Integer;
		acceleratorPosition : Real;
	}
}
