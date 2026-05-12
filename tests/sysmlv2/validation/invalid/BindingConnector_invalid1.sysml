package Example3 {
	part def Fuel;
	port def FuelOutPort {
		out ref fuelSupply : Fuel;
		in ref fuelReturn : Fuel;
	}
	part def FuelTankAssembly {
		port fuelTankPort : FuelOutPort;
	}

	part def Vehicle;
	part vehicle : Vehicle {
		action myAction {
			in myIn;
			out myOut;
		}
		
		part tankAssy {
			port fuelTankPort {
				out ref fuelSupplyOut;
				in ref fuelReturnIn;
			}
		}
		// (TBD) XPECT noErrors --> "Output feature must conform to input feature" at "bind myAction.myOut = tankAssy.fuelTankPort.fuelReturnIn;"
		bind myAction.myOut = tankAssy.fuelTankPort.fuelReturnIn; //InTypes[Part, Object], OutTypes[Anything]
        bind tankAssy.fuelTankPort.fuelSupplyOut = myAction.myIn; //InTypes [Anything], OutTypes [Part, Object]
        
        
        part tankAssy2 : FuelTankAssembly {
			port fuelTankPort redefines FuelTankAssembly::fuelTankPort {
				out ref fuelSupplyOut redefines FuelTankAssembly::fuelTankPort::fuelSupply;
				in ref fuelReturnIn redefines FuelTankAssembly::fuelTankPort::fuelReturn;
			}
		}
		// (TBD) XPECT noErrors --> "Output feature must conform to input feature" at "bind myAction.myOut = tankAssy2.fuelTankPort.fuelReturnIn;"
		bind myAction.myOut = tankAssy2.fuelTankPort.fuelReturnIn; //InTypes[Fuel, Part, Object], OutTypes[Anything]
        bind tankAssy2.fuelTankPort.fuelSupplyOut = myAction.myIn; //InTypes [Anything], OutTypes [Part, Object]
		
	} 
}