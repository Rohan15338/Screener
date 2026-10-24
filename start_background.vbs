' Screener Background Launcher
' Launches Screener in the background using pythonw.exe (no console window)

Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

strScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
strPythonW = WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe")

If Not FSO.FileExists(strPythonW) Then
    ' Fallback to standard pythonw if specific path not found
    strPythonW = "pythonw.exe"
End If

strCommand = """" & strPythonW & """ """ & strScriptDir & "\run.py"" --background"
WshShell.Run strCommand, 0, False
