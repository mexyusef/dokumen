package de.fulgent.callgraph;

import java.io.*;
import java.util.*;
import java.util.function.Function;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;

import org.apache.bcel.classfile.JavaClass;
import org.apache.bcel.classfile.ClassParser;
import org.apache.bcel.util.ClassLoaderRepository;
import org.apache.bcel.classfile.Method;
import java.util.Arrays;
import java.util.stream.Collectors;

public class JCallGraph {

    public static void main(String[] args) {

        Function<ClassParser, ClassVisitor> getClassVisitor = (ClassParser cp) -> {
            try {
                return new ClassVisitor(cp.parse());
            } catch (IOException e) {
                throw new UncheckedIOException(e);
            }
        };

        try {
            for (String arg : args) {

                File f = new File(arg);

                if (!f.exists()) {
                    System.err.println("Jar file " + arg + " does not exist");
                }

                try (JarFile jar = new JarFile(f)) {
                    Stream<JarEntry> entries = stream_enumeration(jar.entries());

                    String methodCalls = entries.flatMap(e -> {
                        if (e.isDirectory() || !e.getName().endsWith(".class"))
                            return (new ArrayList<String>()).stream();

                        ClassParser cp = new ClassParser(arg, e.getName());
                        return getClassVisitor.apply(cp).start().methodCalls().stream();
                    }).map(s -> s + "\n").reduce(new StringBuilder(),
                            StringBuilder::append,
                            StringBuilder::append).toString();
                }
            }
        } catch (IOException e) {
            System.err.println("Error while processing jar: " + e.getMessage());
            e.printStackTrace();
        }
    }

    List<Map<String, List<String>>> list_classname_methods = new ArrayList<>();

    public void cetak() {
        for (Map<String, List<String>> map : list_classname_methods) {
            for (String classname : map.keySet()) {
                List<String> methods = map.get(classname);
                System.out.println(classname + ": " + methods + "\n\n");
            }
        }
    }

    public List<Map<String, List<String>>> get_list_classname_methods() {
        return list_classname_methods;
    }

    public String panggil(String[] args, String[] filter_prefixes) {

        Function<ClassParser, ClassVisitor> getClassVisitor = (ClassParser cp) -> {
            try {
                return new ClassVisitor(cp.parse());
            } catch (IOException e) {
                throw new UncheckedIOException(e);
            }
        };

        try {
            for (String arg : args) {

                File f = new File(arg);

                if (!f.exists()) {
                    System.err.println("Jar file " + arg + " does not exist");
                }

                try (JarFile jar = new JarFile(f)) {
                    Stream<JarEntry> entries = stream_enumeration(jar.entries());

                    String methodCalls = entries
                            .flatMap(e -> {
                                if (e.isDirectory() || !e.getName().endsWith(".class"))
                                    return (new ArrayList<String>()).stream();
                                ClassParser cp = new ClassParser(arg, e.getName());
                                ClassVisitor cv = getClassVisitor.apply(cp);

                                try {
                                    String namakelas = cp.parse().getClassName();

                                    if (Arrays.stream(filter_prefixes).anyMatch(namakelas::startsWith)
                                            && !namakelas.contains("$")) {
                                        list_classname_methods.add(cv.get_classname_methods());
                                    }
                                } catch (IOException ex) {
                                }
                                return cv.start().methodCalls().stream();
                            })
                            .map(s -> s + "\n")
                            .reduce(new StringBuilder(),
                                    StringBuilder::append,
                                    StringBuilder::append)
                            .toString();

                    return methodCalls;
                }
            }
        } catch (IOException e) {
            System.err.println("Error while processing jar: " + e.getMessage());
            e.printStackTrace();
        }
        return "Gagal";
    }

    public static <T> Stream<T> stream_enumeration(Enumeration<T> e) {
        Iterator<T> iterator = new Iterator<T>() {
            public T next() {
                return e.nextElement();
            }

            public boolean hasNext() {
                return e.hasMoreElements();
            }
        };

        Spliterator<T> spliterator = Spliterators.spliteratorUnknownSize(
                iterator, Spliterator.ORDERED);

        return StreamSupport.stream(spliterator, false);
    }

}
