package 'Interface Example' {
	part def Fuel;
	
	port def FuelOutPort;
	port def FuelInPort;
	
	interface def FuelInterface {
		end supplierPort : FuelOutPort;
		end consumerPort : FuelInPort;
	}
	interface def FuelInterface2 {
		end supplierPort : FuelOutPort;
		end consumerPort : FuelInPort;
	}
	interface def FuelInterface3 {
		end supplierPort : FuelOutPort;
		end consumerPort : FuelInPort;
		
		//*XPECT errors ---
			"An interface definition end must be a port." at "end part notPort : Fuel;"
			"Cannot have more than two ends" at "end part notPort : Fuel;"
		--- */
		end part notPort : Fuel;
	}
	
	part def Vehicle;
	part vehicle  {	
		part tankAssy {
			port fuelTankPort : FuelOutPort;
			part fuel : Fuel;
		}
		
		part eng {
			port engineFuelPort : FuelInPort;
		}
		interface fi: FuelInterface connect tankAssy.fuelTankPort to eng.engineFuelPort;
		interface original: FuelInterface, FuelInterface2 connect 
			tankAssy.fuelTankPort to 
			eng.engineFuelPort;
		//XPECT errors --> "An interface must be typed by interface definitions." at "interface opposite : Fuel connect   			x ::> tankAssy.fuelTankPort to  			y ::> eng.engineFuelPort;"
		interface opposite : Fuel connect 
			x ::> tankAssy.fuelTankPort to
			y ::> eng.engineFuelPort;
		//XPECT errors ---> "An interface must be typed by interface definitions." at "interface opposite1 : fi connect eng.engineFuelPort to tankAssy.fuelTankPort;"
		interface opposite1 : fi connect eng.engineFuelPort to tankAssy.fuelTankPort; 
		interface bad {
			//XPECT errors --> "An interface end must be a port." at "end part ::> tankAssy.fuel;"
			// XPECT warnings ---> "Duplicate of inherited member name 'self' from Part, Port" at "end part ::> tankAssy.fuel;"
			end part ::> tankAssy.fuel;
			end port ::> eng.engineFuelPort;
		}
	} 
}