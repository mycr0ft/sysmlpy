// XPECT noErrors ---> ""
package CalculationExample {
	public import ScalarValues::Real;
	public import NumericalFunctions::*;
	
	part def VehiclePart {
		attribute m : Real;
	}
	
	part def Vehicle :> VehiclePart;
	
	part vehicle : Vehicle {		
		part eng : VehiclePart;		
		part trans : VehiclePart;
	}
	
	calc def MassSum {
		in partMasses: Real[0..*];
		return totalMass : Real default sum(partMasses);
	}
	
	calc ms: MassSum {
		in partMasses = (vehicle.eng.m, vehicle.trans.m);
		return totalMass = vehicle.m;
	}
		
	part vehicles[*] = (vehicle, vehicle);
	attribute masses1[*] = (vehicles as VehiclePart).m;
	attribute masses2[*] = (vehicles as vehicle).m;
}
