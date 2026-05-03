// XPECT noErrors ---> ""
package IndividualUsage_Valid {
	part def Vehicle;	
	part def Wheel;
	
	individual def Vehicle_1 :> Vehicle {
		part leftFrontWheel : Wheel;
		part rightFrontWheel : Wheel;
	}
	
	individual def Wheel_1 :> Wheel;
	
	individual vehicle_1 : Vehicle_1 {
		snapshot vehicle_1_t0 {
			individual leftFrontWheel_t0 : Wheel_1 :>> leftFrontWheel;
		}
		
		timeslice vehicle_1_t1 {
			individual rightFrontWheel_t1 : Wheel_1 :>> rightFrontWheel;
		}
		
		first vehicle_1_t0 then vehicle_1_t1;
	}
}
