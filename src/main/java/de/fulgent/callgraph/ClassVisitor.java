
package de.fulgent.callgraph;

import org.apache.bcel.classfile.Constant;
import org.apache.bcel.classfile.ConstantPool;
import org.apache.bcel.classfile.EmptyVisitor;
import org.apache.bcel.classfile.JavaClass;
import org.apache.bcel.classfile.Method;
import org.apache.bcel.generic.ConstantPoolGen;
import org.apache.bcel.generic.MethodGen;
// import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.HashMap;


public class ClassVisitor extends EmptyVisitor {

    private JavaClass clazz;
    private ConstantPoolGen constants;
    private String classReferenceFormat;
    private final DynamicCallManager DCManager = new DynamicCallManager();
    private List<String> methodCalls = new ArrayList<>();

    private List<String> methodNames = new ArrayList<>();

    // ObjectMapper mapper = new ObjectMapper();


    public ClassVisitor(JavaClass jc) {
        clazz = jc;
        constants = new ConstantPoolGen(clazz.getConstantPool());
        classReferenceFormat = "C:" + clazz.getClassName() + " %s";

    }

    public String ambilNamaKelas() {
        return clazz.getClassName();
    }

    public List<String> ambilSemuaMetode() {
        Method[] methods = clazz.getMethods();        
        
        for (Method method : methods) {
            
            String namametode = method.getName();

            if (namametode.contains("$")) {
                continue;
            }

            methodNames.add(namametode);

        }
        return methodNames;
    }


    public Map<String, List<String>> get_classname_methods() {
        Map<String, List<String>> classNameMethods = new HashMap<>();
        String className = ambilNamaKelas();
        List<String> methods = ambilSemuaMetode();
        classNameMethods.put(className, methods);
        return classNameMethods;
    }

    public void visitJavaClass(JavaClass jc) {
        jc.getConstantPool().accept(this);
        Method[] methods = jc.getMethods();
        for (int i = 0; i < methods.length; i++) {
            Method method = methods[i];
            DCManager.retrieveCalls(method, jc);
            DCManager.linkCalls(method);
            method.accept(this);
        }
    }

    public void visitConstantPool(ConstantPool constantPool) {
        for (int i = 0; i < constantPool.getLength(); i++) {
            Constant constant = constantPool.getConstant(i);
            if (constant == null)
                continue;
            if (constant.getTag() == 7) {
                String referencedClass = constantPool.constantToString(constant);
                // System.out.println(String.format(classReferenceFormat, referencedClass));
            }
        }
    }

    public void visitMethod(Method method) {
        MethodGen mg = new MethodGen(method, clazz.getClassName(), constants);
        MethodVisitor visitor = new MethodVisitor(mg, clazz);
        methodCalls.addAll(visitor.start());
    }

    public ClassVisitor start() {
        visitJavaClass(clazz);
        return this;
    }

    public List<String> methodCalls() {
        return this.methodCalls;
    }
}
