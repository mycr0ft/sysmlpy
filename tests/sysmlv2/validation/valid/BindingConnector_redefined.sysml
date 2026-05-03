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
	part def FuelPump;
	part def FuelTank;
	
	part vehicle : Vehicle {	
		part tank : FuelTankAssembly {
			port fuelTankPort0 redefines FuelTankAssembly::fuelTankPort {
				out ref fuelSupply redefines FuelTankAssembly::fuelTankPort::fuelSupply;
				in ref redefines fuelReturn;
			}
			port redefines FuelTankAssembly::fuelTankPort {
				out ref fuelSupply redefines FuelTankAssembly::fuelTankPort::fuelSupply;
			}
			
			bind fuelTankPort0.fuelSupply = pump.pumpOut;
			bind fuelTankPort0.fuelReturn = tank.fuelIn;
			bind fuelTankPort.fuelSupply = pump.pumpOut;
					
			part pump : FuelPump {
				out ref pumpOut : Fuel;
				in ref pumpIn : Fuel;
			}
			
			part tank : FuelTank {
				in ref fuelOut : Fuel;
				in ref fuelIn : Fuel;
			}
		}
	} 
}
