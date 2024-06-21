Sub RunPythonScript()
    On Error GoTo ErrorHandler
    
    Dim objShell As Object
    Set objShell = VBA.CreateObject("WScript.Shell")
    
    ' Get the path of the current workbook
    Dim workbookPath As String
    workbookPath = ThisWorkbook.Path
    
    ' Define the relative path to the executable
    Dim exePath As String
    exePath = workbookPath & "\dist\process_data.exe"
    
    ' Command to execute the script
    Dim command As String
    command = """" & exePath & """"
    
    ' Log file path
    Dim logFile As String
    logFile = workbookPath & "\vba_log.txt"
    
    ' Write to log file
    Dim fso As Object
    Set fso = CreateObject("Scripting.FileSystemObject")
    Dim logStream As Object
    Set logStream = fso.OpenTextFile(logFile, 8, True)
    logStream.WriteLine "Running command: " & command
    logStream.Close
    
    ' Run the command and capture output
    Dim returnCode As Integer
    returnCode = objShell.Run(command, 1, True)
    
    ' Confirm the output
    Dim outputFile As String
    outputFile = workbookPath & "\output.xlsx"
    
    If Dir(outputFile) <> "" Then
        MsgBox "Output file created successfully: " & outputFile
    Else
        MsgBox "Failed to create output file: " & outputFile & vbCrLf & "Check log file: " & logFile
    End If
    
    Exit Sub
    
ErrorHandler:
    MsgBox "An error occurred: " & Err.Description
    ' Write error to log file
    Set logStream = fso.OpenTextFile(logFile, 8, True)
    logStream.WriteLine "Error: " & Err.Description
    logStream.Close
End Sub
