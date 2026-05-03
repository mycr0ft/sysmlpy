// XPECT noErrors ---> ""
package 'Interface Example' {
	attribute def Temp;
	part def Fuel;

	port def FuelOutPort {
		attribute temperature : Temp;
		out ref fuelSupply : Fuel;
		in ref fuelReturn : Fuel;
	}
	
	port def FuelInPort {
		attribute temperature : Temp;
		in ref fuelSupply : Fuel;
		out ref fuelReturn : Fuel;
	}
	
	part def FuelTankAssembly {
		port fuelTankPort : FuelOutPort;
	}
	
	part def Engine {
		port engineFuelPort : FuelInPort;
	}
	
	part def Vehicle;
	
	interface def FuelInterface {
		end supplierPort : FuelOutPort;
		end consumerPort : FuelInPort;
		flow supplierPort.fuelSupply to consumerPort.fuelSupply;
		flow consumerPort.fuelReturn to supplierPort.fuelReturn;
	}
	
	part vehicle : Vehicle {	
		part tankAssy : FuelTankAssembly {
			port redefines fuelTankPort;
		}
		
		part eng : Engine {
			port redefines engineFuelPort;
		}
		interface FuelInterface connect 
			supplierPort ::> tankAssy.fuelTankPort to 
			consumerPort ::> eng.engineFuelPort;
	} 
}
