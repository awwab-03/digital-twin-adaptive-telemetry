package com.github.luben.zstd;
// Shim: Maven Central unreachable in our environment. compress() is identity;
// the real zstd (level 3, same as zstd-jni default) is applied afterwards in Python.
public class Zstd {
  public static byte[] compress(byte[] in){ return in.clone(); }
  public static byte[] decompress(byte[] in, int size){ return in.clone(); }
}
