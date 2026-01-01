import leekscript.runner.*;
import leekscript.runner.values.*;
import leekscript.runner.classes.*;
import leekscript.common.*;

public class AI_1 extends AI {
public AI_1() throws LeekRunException {
super(1, 4);
}
public void staticInit() throws LeekRunException {
}
public Object runIA(Session session) throws LeekRunException {
resetCounter();
Object u_x = ops(((Object) (1l)), 1);
session.setVariable(AI_1.this, "x", u_x);
return null;
}
protected String getAIString() { return "<snippet 1>";}
protected String[] getErrorFiles() { return new String[] {"<snippet 1>", };}

protected int[] getErrorFilesID() { return new int[] {1, };}

}
