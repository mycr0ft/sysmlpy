	
	
// XPECT noErrors ---> ""
package KernelLibraryTest {

	public import ScalarValues::**; //public import ScalarValues::Real;
	public import NumericalFunctions::**; //public import NumericalFunctions::sum;
	public import ISQ::**; //ISQ::MassValue
	
	part vehicle {
		attribute m: Real;
		attribute totalMass: MassValue;
		
		part eng {
			attribute m: Real;
		}
		
		part trans {
			attribute m: Real;
		}
	}
	
	calc def MassSum {
		in partMasses : Real[0..*];
		return totalMass : Real;
		
		sum(partMasses)
	}
	
	calc ms: MassSum {
		in partMasses = (vehicle.eng.m, vehicle.trans.m);
	}
	
	totalMass = vehicle.m;

}

