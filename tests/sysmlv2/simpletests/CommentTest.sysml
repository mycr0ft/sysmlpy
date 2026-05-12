// XPECT noErrors ---> ""
 
  /* AAA */
  //a lexical comment ("note") is not a part of model
package Comments {
	// inside package
	/*
*AAA
 * BBB*/	
 /*
    *
    *
    * AAA  ***   
    *BBB
    								*/

   /*
 *       AAAA
 *       BBBB           */	
 /* AAAA
 
 
  * BBBB
 *
 * CCCC
 */
 /*
 * AAAA
 * BBBB
 *    CCC DDD    
 */
	
	/* comment inside a package */
	doc /* Documentation about Package */
	comment cmt /* Named Comment */	
	comment cmt_cmtc about cmt /* Comment about Comment */
	
	part def C {
		doc /* Documentation in Part Def */
		comment /* Comment in Part Def */
		comment about Comments /* Comment about Package */
	}
	/* abc */
	part def A;
}