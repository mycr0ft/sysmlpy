// XPECT noErrors ---> ""
package Example2 {
	part def Fuel;
	port def FuelOutPort {
		out ref fuelSupply : Fuel;
		in ref fuelReturn : Fuel;
	}
	part def FuelTankAssembly {
		port fuelTankPort : FuelOutPort;
	}

	part def Vehicle;
	part def FuelPump {
		out ref pumpOut : Fuel;
		in ref pumpIn : Fuel;
	}
	part def FuelTank {
		in ref fuelOut : Fuel;
		in ref fuelIn : Fuel;
	}
	
	part vehicle : Vehicle {	
		part tank : FuelTankAssembly {
			bind fuelTankPort.fuelSupply = pump.pumpOut;
			bind fuelTankPort.fuelReturn = tank.fuelIn;
			bind fuelTankPort.fuelSupply = pump.pumpOut;
					
			part pump : FuelPump;			
			part tank : FuelTank;
		}
	} 
}
