"""Module for testing DML returning clauses."""

import sys

class TestDMLReturning(BaseTestCase):

    def testInsert(self):
        "test insert statement (single row) with DML returning"
        self.cursor.execute("truncate table TestTempTable")
        intVal = 5
        strVal = "A test string"
        intVar = self.cursor.var(cx_Oracle.NUMBER)
        strVar = self.cursor.var(str)
        self.cursor.execute("""
                insert into TestTempTable
                values (:intVal, :strVal)
                returning IntCol, StringCol into :intVar, :strVar""",
                intVal = intVal,
                strVal = strVal,
                intVar = intVar,
                strVar = strVar)
        self.assertEqual(intVar.values, [intVal])
        self.assertEqual(strVar.values, [strVal])
        cx_Oracle.__future__.dml_ret_array_val = True
        try:
            self.assertEqual(intVar.values, [[intVal]])
            self.assertEqual(strVar.values, [[strVal]])
        finally:
            cx_Oracle.__future__.dml_ret_array_val = False

    def testInsertMany(self):
        "test insert statement (multiple rows) with DML returning"
        self.cursor.execute("truncate table TestTempTable")
        intValues = [5, 8, 17, 24, 6]
        strValues = ["Test 5", "Test 8", "Test 17", "Test 24", "Test 6"]
        intVar = self.cursor.var(cx_Oracle.NUMBER, arraysize = len(intValues))
        strVar = self.cursor.var(str, arraysize = len(intValues))
        self.cursor.setinputsizes(None, None, intVar, strVar)
        data = list(zip(intValues, strValues))
        self.cursor.executemany("""
                insert into TestTempTable
                values (:intVal, :strVal)
                returning IntCol, StringCol into :intVar, :strVar""", data)
        self.assertEqual(intVar.values, [intValues[0]])
        self.assertEqual(strVar.values, [strValues[0]])
        cx_Oracle.__future__.dml_ret_array_val = True
        try:
            self.assertEqual(intVar.values, [[v] for v in intValues])
            self.assertEqual(strVar.values, [[v] for v in strValues])
        finally:
            cx_Oracle.__future__.dml_ret_array_val = False

    def testInsertWithSmallSize(self):
        "test insert statement with DML returning into too small a variable"
        self.cursor.execute("truncate table TestTempTable")
        intVal = 6
        strVal = "A different test string"
        intVar = self.cursor.var(cx_Oracle.NUMBER)
        strVar = self.cursor.var(str, 2)
        parameters = dict(intVal = intVal, strVal = strVal, intVar = intVar,
                strVar = strVar)
        self.assertRaises(cx_Oracle.DatabaseError, self.cursor.execute, """
                insert into TestTempTable
                values (:intVal, :strVal)
                returning IntCol, StringCol into :intVar, :strVar""",
                parameters)

    def testUpdateSingleRow(self):
        "test update single row statement with DML returning"
        intVal = 7
        strVal = "The updated value of the string"
        self.cursor.execute("truncate table TestTempTable")
        self.cursor.execute("insert into TestTempTable values (:1, :2)",
                (intVal, "The initial value of the string"))
        intVar = self.cursor.var(cx_Oracle.NUMBER)
        strVar = self.cursor.var(str)
        self.cursor.execute("""
                update TestTempTable set
                    StringCol = :strVal
                where IntCol = :intVal
                returning IntCol, StringCol into :intVar, :strVar""",
                intVal = intVal,
                strVal = strVal,
                intVar = intVar,
                strVar = strVar)
        self.assertEqual(intVar.values, [intVal])
        self.assertEqual(strVar.values, [strVal])
        cx_Oracle.__future__.dml_ret_array_val = True
        try:
            self.assertEqual(intVar.values, [[intVal]])
            self.assertEqual(strVar.values, [[strVal]])
        finally:
            cx_Oracle.__future__.dml_ret_array_val = False

    def testUpdateNoRows(self):
        "test update no rows statement with DML returning"
        intVal = 8
        strVal = "The updated value of the string"
        self.cursor.execute("truncate table TestTempTable")
        self.cursor.execute("insert into TestTempTable values (:1, :2)",
                (intVal, "The initial value of the string"))
        intVar = self.cursor.var(cx_Oracle.NUMBER)
        strVar = self.cursor.var(str)
        self.cursor.execute("""
                update TestTempTable set
                    StringCol = :strVal
                where IntCol = :intVal
                returning IntCol, StringCol into :intVar, :strVar""",
                intVal = intVal + 1,
                strVal = strVal,
                intVar = intVar,
                strVar = strVar)
        self.assertEqual(intVar.values, [])
        self.assertEqual(strVar.values, [])
        cx_Oracle.__future__.dml_ret_array_val = True
        try:
            self.assertEqual(intVar.values, [[]])
            self.assertEqual(strVar.values, [[]])
        finally:
            cx_Oracle.__future__.dml_ret_array_val = False

    def testUpdateMultipleRows(self):
        "test update multiple rows statement with DML returning"
        self.cursor.execute("truncate table TestTempTable")
        for i in (8, 9, 10):
            self.cursor.execute("insert into TestTempTable values (:1, :2)",
                    (i, "The initial value of string %d" % i))
        intVar = self.cursor.var(cx_Oracle.NUMBER)
        strVar = self.cursor.var(str)
        self.cursor.execute("""
                update TestTempTable set
                    IntCol = IntCol + 15,
                    StringCol = 'The final value of string ' || to_char(IntCol)
                returning IntCol, StringCol into :intVar, :strVar""",
                intVar = intVar,
                strVar = strVar)
        self.assertEqual(self.cursor.rowcount, 3)
        self.assertEqual(intVar.values, [23, 24, 25])
        self.assertEqual(strVar.values, [
                "The final value of string 8",
                "The final value of string 9",
                "The final value of string 10"
        ])
        cx_Oracle.__future__.dml_ret_array_val = True
        try:
            self.assertEqual(intVar.values, [[23, 24, 25]])
            self.assertEqual(strVar.values, [[
                    "The final value of string 8",
                    "The final value of string 9",
                    "The final value of string 10"
            ]])
        finally:
            cx_Oracle.__future__.dml_ret_array_val = False

    def testUpdateMultipleRowsExecuteMany(self):
        "test update multiple rows with DML returning (executeMany)"
        self.cursor.execute("truncate table TestTempTable")
        for i in range(1, 11):
            self.cursor.execute("insert into TestTempTable values (:1, :2)",
                    (i, "The initial value of string %d" % i))
        intVar = self.cursor.var(cx_Oracle.NUMBER, arraysize = 3)
        strVar = self.cursor.var(str, arraysize = 3)
        self.cursor.setinputsizes(None, intVar, strVar)
        self.cursor.executemany("""
                update TestTempTable set
                    IntCol = IntCol + 25,
                    StringCol = 'Updated value of string ' || to_char(IntCol)
                where IntCol < :inVal
                returning IntCol, StringCol into :intVar, :strVar""",
                [[3], [8], [11]])
        self.assertEqual(intVar.values, [26, 27])
        self.assertEqual(strVar.values, [
                "Updated value of string 1",
                "Updated value of string 2"
        ])
        cx_Oracle.__future__.dml_ret_array_val = True
        try:
            self.assertEqual(intVar.values, [
                    [26, 27],
                    [28, 29, 30, 31, 32],
                    [33, 34, 35]
            ])
            self.assertEqual(strVar.values, [
                    [ "Updated value of string 1",
                      "Updated value of string 2" ],
                    [ "Updated value of string 3",
                      "Updated value of string 4",
                      "Updated value of string 5",
                      "Updated value of string 6",
                      "Updated value of string 7" ],
                    [ "Updated value of string 8",
                      "Updated value of string 9",
                      "Updated value of string 10" ]
            ])
        finally:
            cx_Oracle.__future__.dml_ret_array_val = False

    def testInsertAndReturnObject(self):
        "test inserting an object with DML returning"
        typeObj = self.connection.gettype("UDT_OBJECT")
        stringValue = "The string that will be verified"
        obj = typeObj.newobject()
        obj.STRINGVALUE = stringValue
        outVar = self.cursor.var(cx_Oracle.OBJECT, typename = "UDT_OBJECT")
        self.cursor.execute("""
                insert into TestObjects (IntCol, ObjectCol)
                values (4, :obj)
                returning ObjectCol into :outObj""",
                obj = obj, outObj = outVar)
        result = outVar.getvalue()
        self.assertEqual(result.STRINGVALUE, stringValue)
        cx_Oracle.__future__.dml_ret_array_val = True
        try:
            result, = outVar.getvalue()
            self.assertEqual(result.STRINGVALUE, stringValue)
        finally:
            cx_Oracle.__future__.dml_ret_array_val = False
        self.connection.rollback()

