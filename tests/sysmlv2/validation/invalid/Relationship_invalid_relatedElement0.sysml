package Relationship_invalid_relatedElement {
	part v {
		part b0;
		// XPECT errors ---> "Must have at least two related elements" at "connection { end ::> b0; }"
		connection { end ::> b0; }
		
		abstract connection { end ::> b0; }	
	} 
}