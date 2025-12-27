"""
Test Python file with intentional bugs for CodeGuard testing
"""

import os
import pickle

# Security Issues
password = "admin123"  # Hardcoded password
api_key = "sk-12345"  # Hardcoded API key

def unsafe_eval(user_input):
    # Command injection
    result = eval(user_input)  # Dangerous eval
    return result

def sql_injection_vulnerable(user_id):
    # SQL injection
    query = "SELECT * FROM users WHERE id = " + user_id  # String concatenation
    return query

def command_injection(filename):
    # Command injection
    os.system(f"cat {filename}")  # Shell injection

def pickle_vulnerability(data):
    # Insecure deserialization
    obj = pickle.loads(data)  # Unsafe pickle
    return obj

# Logic Errors
def division_bug(a, b):
    return a / b  # No zero check

def off_by_one(arr):
    # Off-by-one error
    for i in range(len(arr) + 1):  # Will cause index error
        print(arr[i])

# Performance Issues
def slow_concat():
    result = ""
    for i in range(10000):
        result += str(i)  # Inefficient string concatenation
    return result

def nested_loops(n):
    # O(n^2) algorithm
    for i in range(n):
        for j in range(n):
            print(i * j)

# Code Quality Issues
def long_function_with_many_issues(a, b, c, d, e, f):  # Too many parameters
    # Function is too long
    x = a + b
    y = c + d
    z = e + f
    
    # Duplicate code
    if x > 10:
        print("x is large")
        result = x * 2
    elif y > 10:
        print("y is large")
        result = y * 2  # Duplicate
    elif z > 10:
        print("z is large")
        result = z * 2  # Duplicate
    
    # Magic numbers
    if x > 42:  # Magic number
        return 3.14159  # Another magic number
    
    return result

# Resource Management Issues
def file_leak():
    f = open("test.txt", "r")  # File not closed
    data = f.read()
    return data

# Mutable default argument
def append_to_list(item, lst=[]):  # Mutable default
    lst.append(item)
    return lst

# Bare except
def catch_all_errors():
    try:
        risky_operation()
    except:  # Bare except
        pass

# Wrong equality check
def check_none(value):
    if value == None:  # Should use 'is None'
        return True
    return False
