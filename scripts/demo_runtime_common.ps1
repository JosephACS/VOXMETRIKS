#requires -Version 5.1
<#
.SYNOPSIS
  Pure helpers for VOXMETRIKS demo runtime host compatibility.
  No side effects on import (no process start/stop, no file writes).
#>

function Normalize-DemoIdentityText {
    param([string]$Value)
    if ($null -eq $Value) { return '' }
    $t = $Value.Trim().ToLowerInvariant()
    $t = $t -replace '/', '\'
    $t = $t -replace '\s+', ' '
    return $t
}

function Test-DemoPathMatch {
    param(
        [string]$Candidate,
        [string]$ExpectedLower
    )
    if ([string]::IsNullOrWhiteSpace($Candidate) -or [string]::IsNullOrWhiteSpace($ExpectedLower)) {
        return $false
    }
    return (Normalize-DemoIdentityText $Candidate).Contains((Normalize-DemoIdentityText $ExpectedLower))
}

function Get-PortListenerPid {
    <#
      Returns owning PID of a TCP LISTENING socket on $Port, or $null.
      -ForceNetstat skips Get-NetTCPConnection (productive fallback path for tests).
    #>
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port,
        [switch]$ForceNetstat
    )

    if (-not $ForceNetstat) {
        try {
            $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
                Select-Object -First 1
            if ($conn -and $conn.OwningProcess) {
                return [int]$conn.OwningProcess
            }
        } catch {
            # Fall through to netstat.
        }
    }

    $portToken = ':' + [string]$Port
    $raw = & netstat.exe -ano -p tcp 2>$null
    if (-not $raw) { return $null }

    foreach ($line in @($raw)) {
        if ($line -notmatch '(?i)\bLISTENING\b') { continue }
        if ($line -notmatch '(?i)^\s*TCP\s+(\S+)\s+\S+\s+LISTENING\s+(\d+)\s*$') { continue }
        $localAddr = [string]$Matches[1]
        $owningPid = [int]$Matches[2]
        if ($owningPid -le 0) { continue }

        if ($localAddr.EndsWith($portToken, [System.StringComparison]::Ordinal)) {
            $prefix = $localAddr.Substring(0, $localAddr.Length - $portToken.Length)
            if ($prefix.Length -eq 0) { continue }
            $last = $prefix[$prefix.Length - 1]
            # IPv4 ends with digit; IPv6 bracket form ends with ']'.
            if ($last -match '[0-9\]]') {
                return $owningPid
            }
        }
    }
    return $null
}

function Get-DemoProcessHandleInfo {
    <#
      Handle-based identity only (no WMI). Returns $null if process gone or path/start unavailable.
    #>
    param([int]$ProcessId)
    if ($ProcessId -le 0) { return $null }
    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if (-not $proc) { return $null }
    if (-not $proc.StartTime) { return $null }

    $exe = $null
    try {
        if ($proc.Path) { $exe = [string]$proc.Path }
    } catch { }
    if ([string]::IsNullOrWhiteSpace($exe)) {
        try {
            $exe = [string]$proc.MainModule.FileName
        } catch { }
    }
    if ([string]::IsNullOrWhiteSpace($exe)) { return $null }

    return [pscustomobject]@{
        Pid            = $ProcessId
        Name           = [string]$proc.ProcessName
        StartTimeUtc   = $proc.StartTime.ToUniversalTime().ToString('o')
        ExecutablePath = $exe
    }
}

function Get-DemoProcessWmiInfo {
    <#
      Optional WMI/CIM enrichment. Returns $null on failure (restricted hosts).
    #>
    param([int]$ProcessId)
    if ($ProcessId -le 0) { return $null }
    try {
        $wmi = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction Stop
    } catch {
        return $null
    }
    if (-not $wmi) { return $null }
    return [pscustomobject]@{
        Pid             = $ProcessId
        CommandLine     = $(if ($wmi.CommandLine) { [string]$wmi.CommandLine } else { '' })
        ExecutablePath  = $(if ($wmi.ExecutablePath) { [string]$wmi.ExecutablePath } else { '' })
        ParentProcessId = $(if ($wmi.ParentProcessId) { [int]$wmi.ParentProcessId } else { 0 })
    }
}

function Test-DemoHttpStatus200 {
    param(
        [string]$Url,
        [int]$TimeoutSec = 3
    )
    try {
        $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec -ErrorAction Stop
        return ($resp.StatusCode -eq 200)
    } catch {
        return $false
    }
}

function Test-VoxmetriksHealthResponse {
    param(
        [string]$Url = 'http://127.0.0.1:8000/health',
        [int]$TimeoutSec = 3
    )
    try {
        $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec -ErrorAction Stop
        if ($resp.StatusCode -ne 200) { return $false }
        $json = $resp.Content | ConvertFrom-Json
        if (-not $json) { return $false }
        if ($null -eq $json.status) { return $false }
        if ($null -eq $json.db_connected) { return $false }
        if ($null -eq $json.tables_ok) { return $false }
        if ($null -eq $json.etl_status) { return $false }
        if ($null -eq $json.gold_ready) { return $false }
        return $true
    } catch {
        return $false
    }
}

function Test-SessionOwnedHandleMatch {
    <#
      Session-launched process: PID + StartTimeUtc + executablePath from live handle.
      Does not require WMI/commandLine.
    #>
    param(
        [object]$HandleInfo,
        [object]$Record
    )
    if (-not $HandleInfo -or -not $Record) { return $false }
    if ([int]$HandleInfo.Pid -ne [int]$Record.Pid) { return $false }
    if ([string]$HandleInfo.StartTimeUtc -ne [string]$Record.StartTimeUtc) { return $false }

    $liveExe = Normalize-DemoIdentityText ([string]$HandleInfo.ExecutablePath)
    $metaExe = Normalize-DemoIdentityText ([string]$Record.ExecutablePath)
    if ([string]::IsNullOrWhiteSpace($liveExe) -or [string]::IsNullOrWhiteSpace($metaExe)) {
        return $false
    }
    return ($liveExe -eq $metaExe)
}

function Test-StrictPortWorkerIdentity {
    <#
      Port-discovered arbitrary process: requires WMI commandLine.
      Missing/empty commandLine => refuse (do not kill).
    #>
    param(
        [object]$WmiInfo,
        [object]$HandleInfo,
        [ValidateSet('backend', 'frontend')]
        [string]$Kind,
        [string]$RepoRootLower,
        [string]$VenvDirLower,
        [string]$VenvPythonLower,
        [string]$FrontendDirLower
    )
    if (-not $WmiInfo -or -not $HandleInfo) { return $false }
    $cmd = [string]$WmiInfo.CommandLine
    if ([string]::IsNullOrWhiteSpace($cmd)) { return $false }

    $name = ([string]$HandleInfo.Name).ToLowerInvariant()
    $exe = [string]$HandleInfo.ExecutablePath
    if ([string]::IsNullOrWhiteSpace($exe) -and $WmiInfo.ExecutablePath) {
        $exe = [string]$WmiInfo.ExecutablePath
    }

    if ($Kind -eq 'backend') {
        if ($name -notmatch '^(python|pythonw)$') { return $false }
        $exeInVenv = Test-DemoPathMatch $exe $VenvDirLower
        $cmdInVenv = (Test-DemoPathMatch $cmd $VenvPythonLower) -or (Test-DemoPathMatch $cmd $VenvDirLower)
        if (-not ($exeInVenv -or $cmdInVenv)) { return $false }
        if ($cmd -notmatch 'uvicorn') { return $false }
        if ($cmd -notmatch 'app\.main') { return $false }
        if (-not (Test-DemoPathMatch $cmd $RepoRootLower)) { return $false }
        return $true
    }

    if ($Kind -eq 'frontend') {
        if ($name -ne 'node') { return $false }
        if (-not (Test-DemoPathMatch $cmd $FrontendDirLower)) { return $false }
        if ($cmd -notmatch 'ng serve|ng\.js|@angular[/\\]cli') { return $false }
        return $true
    }
    return $false
}

function Test-DemoProcessRunning {
    param([int]$ProcessId)
    if ($ProcessId -le 0) { return $false }
    return [bool](Get-Process -Id $ProcessId -ErrorAction SilentlyContinue)
}

function Test-DemoExecutablePathEquals {
    param(
        [string]$Left,
        [string]$Right
    )
    if ([string]::IsNullOrWhiteSpace($Left) -or [string]::IsNullOrWhiteSpace($Right)) {
        return $false
    }
    try {
        $a = [System.IO.Path]::GetFullPath($Left.Trim())
        $b = [System.IO.Path]::GetFullPath($Right.Trim())
    } catch {
        return $false
    }
    return [string]::Equals($a, $b, [System.StringComparison]::OrdinalIgnoreCase)
}

function Test-DemoArtifactPathAllowed {
    <#
      Artifact must resolve to a direct child file of PidDir (GetFullPath).
      Rejects .., external paths, subdirectories, PidDir itself.
    #>
    param(
        [string]$ArtifactPath,
        [string]$PidDir
    )
    if ([string]::IsNullOrWhiteSpace($ArtifactPath) -or [string]::IsNullOrWhiteSpace($PidDir)) {
        return $false
    }
    try {
        $pidFull = [System.IO.Path]::GetFullPath($PidDir)
        $artFull = [System.IO.Path]::GetFullPath($ArtifactPath)
    } catch {
        return $false
    }
    if ([string]::Equals($artFull, $pidFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $false
    }
    $parent = [System.IO.Path]::GetDirectoryName($artFull)
    if ([string]::IsNullOrWhiteSpace($parent)) { return $false }
    if (-not [string]::Equals($parent, $pidFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $false
    }
    $leaf = [System.IO.Path]::GetFileName($artFull)
    if ([string]::IsNullOrWhiteSpace($leaf)) { return $false }
    if ($leaf -match '[\\/]') { return $false }
    return $true
}

function Ensure-DemoNativeStartType {
    # Versioned type name so updated P/Invoke definitions reload in new processes.
    if ('DemoNativeStartV3' -as [type]) { return }
    Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;

public static class DemoNativeStartV3 {
    [StructLayout(LayoutKind.Sequential)]
    public struct SECURITY_ATTRIBUTES {
        public int nLength;
        public IntPtr lpSecurityDescriptor;
        public int bInheritHandle;
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct STARTUPINFO {
        public int cb;
        public IntPtr lpReserved;
        public IntPtr lpDesktop;
        public IntPtr lpTitle;
        public int dwX;
        public int dwY;
        public int dwXSize;
        public int dwYSize;
        public int dwXCountChars;
        public int dwYCountChars;
        public int dwFillAttribute;
        public int dwFlags;
        public short wShowWindow;
        public short cbReserved2;
        public IntPtr lpReserved2;
        public IntPtr hStdInput;
        public IntPtr hStdOutput;
        public IntPtr hStdError;
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct STARTUPINFOEX {
        public STARTUPINFO StartupInfo;
        public IntPtr lpAttributeList;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct PROCESS_INFORMATION {
        public IntPtr hProcess;
        public IntPtr hThread;
        public int dwProcessId;
        public int dwThreadId;
    }

    const int STARTF_USESTDHANDLES = 0x00000100;
    const int STARTF_USESHOWWINDOW = 0x00000001;
    const int CREATE_NO_WINDOW = 0x08000000;
    const uint EXTENDED_STARTUPINFO_PRESENT = 0x00080000;
    const short SW_HIDE = 0;
    const uint GENERIC_WRITE = 0x40000000;
    const uint GENERIC_READ = 0x80000000;
    const uint FILE_SHARE_READ = 0x00000001;
    const uint CREATE_ALWAYS = 2;
    const uint OPEN_EXISTING = 3;
    const uint FILE_ATTRIBUTE_NORMAL = 0x80;
    static readonly IntPtr InvalidHandle = new IntPtr(-1);
    static readonly IntPtr PROC_THREAD_ATTRIBUTE_HANDLE_LIST = new IntPtr(0x20002);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    static extern IntPtr CreateFile(
        string lpFileName,
        uint dwDesiredAccess,
        uint dwShareMode,
        ref SECURITY_ATTRIBUTES lpSecurityAttributes,
        uint dwCreationDisposition,
        uint dwFlagsAndAttributes,
        IntPtr hTemplateFile);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    static extern bool CreateProcess(
        string lpApplicationName,
        StringBuilder lpCommandLine,
        IntPtr lpProcessAttributes,
        IntPtr lpThreadAttributes,
        bool bInheritHandles,
        uint dwCreationFlags,
        IntPtr lpEnvironment,
        string lpCurrentDirectory,
        ref STARTUPINFOEX lpStartupInfo,
        out PROCESS_INFORMATION lpProcessInformation);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool CloseHandle(IntPtr hObject);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool InitializeProcThreadAttributeList(
        IntPtr lpAttributeList,
        int dwAttributeCount,
        int dwFlags,
        ref IntPtr lpSize);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool UpdateProcThreadAttribute(
        IntPtr lpAttributeList,
        uint dwFlags,
        IntPtr Attribute,
        IntPtr lpValue,
        IntPtr cbSize,
        IntPtr lpPreviousValue,
        IntPtr lpReturnSize);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern void DeleteProcThreadAttributeList(IntPtr lpAttributeList);

    public static int Start(string exe, string args, string cwd, string stdoutPath, string stderrPath) {
        var sa = new SECURITY_ATTRIBUTES();
        sa.nLength = Marshal.SizeOf(typeof(SECURITY_ATTRIBUTES));
        sa.bInheritHandle = 1;
        sa.lpSecurityDescriptor = IntPtr.Zero;

        IntPtr hOut = InvalidHandle;
        IntPtr hErr = InvalidHandle;
        IntPtr hNul = InvalidHandle;
        IntPtr attrList = IntPtr.Zero;
        bool attrListInitialized = false;

        try {
            hOut = CreateFile(stdoutPath, GENERIC_WRITE, FILE_SHARE_READ, ref sa, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, IntPtr.Zero);
            if (hOut == InvalidHandle) throw new Win32Exception(Marshal.GetLastWin32Error());
            hErr = CreateFile(stderrPath, GENERIC_WRITE, FILE_SHARE_READ, ref sa, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, IntPtr.Zero);
            if (hErr == InvalidHandle) throw new Win32Exception(Marshal.GetLastWin32Error());
            hNul = CreateFile("NUL", GENERIC_READ, FILE_SHARE_READ, ref sa, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, IntPtr.Zero);
            if (hNul == InvalidHandle) throw new Win32Exception(Marshal.GetLastWin32Error());

            IntPtr size = IntPtr.Zero;
            InitializeProcThreadAttributeList(IntPtr.Zero, 1, 0, ref size);
            if (size == IntPtr.Zero || size.ToInt64() <= 0) {
                throw new InvalidOperationException("InitializeProcThreadAttributeList sizing returned a non-positive buffer size.");
            }

            attrList = Marshal.AllocHGlobal(size);
            if (!InitializeProcThreadAttributeList(attrList, 1, 0, ref size)) {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }
            attrListInitialized = true;

            IntPtr handleList = Marshal.AllocHGlobal(IntPtr.Size * 3);
            try {
                Marshal.WriteIntPtr(handleList, 0 * IntPtr.Size, hOut);
                Marshal.WriteIntPtr(handleList, 1 * IntPtr.Size, hErr);
                Marshal.WriteIntPtr(handleList, 2 * IntPtr.Size, hNul);

                if (!UpdateProcThreadAttribute(
                    attrList,
                    0,
                    PROC_THREAD_ATTRIBUTE_HANDLE_LIST,
                    handleList,
                    new IntPtr(IntPtr.Size * 3),
                    IntPtr.Zero,
                    IntPtr.Zero)) {
                    throw new Win32Exception(Marshal.GetLastWin32Error());
                }

                var siex = new STARTUPINFOEX();
                siex.StartupInfo.cb = Marshal.SizeOf(typeof(STARTUPINFOEX));
                siex.StartupInfo.dwFlags = STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
                siex.StartupInfo.wShowWindow = SW_HIDE;
                siex.StartupInfo.hStdOutput = hOut;
                siex.StartupInfo.hStdError = hErr;
                siex.StartupInfo.hStdInput = hNul;
                siex.lpAttributeList = attrList;

                var cmd = new StringBuilder();
                if (exe.IndexOf(' ') >= 0) {
                    cmd.Append('"').Append(exe).Append('"');
                } else {
                    cmd.Append(exe);
                }
                if (!string.IsNullOrEmpty(args)) {
                    cmd.Append(' ');
                    cmd.Append(args);
                }

                PROCESS_INFORMATION pi;
                bool ok = CreateProcess(
                    null,
                    cmd,
                    IntPtr.Zero,
                    IntPtr.Zero,
                    true,
                    ((uint)CREATE_NO_WINDOW) | EXTENDED_STARTUPINFO_PRESENT,
                    IntPtr.Zero,
                    cwd,
                    ref siex,
                    out pi);

                if (!ok) throw new Win32Exception(Marshal.GetLastWin32Error());

                int pid = pi.dwProcessId;
                CloseHandle(pi.hProcess);
                CloseHandle(pi.hThread);
                return pid;
            } finally {
                Marshal.FreeHGlobal(handleList);
            }
        } finally {
            if (attrListInitialized) {
                DeleteProcThreadAttributeList(attrList);
            }
            if (attrList != IntPtr.Zero) {
                Marshal.FreeHGlobal(attrList);
            }
            if (hOut != InvalidHandle) {
                CloseHandle(hOut);
            }
            if (hErr != InvalidHandle) {
                CloseHandle(hErr);
            }
            if (hNul != InvalidHandle) {
                CloseHandle(hNul);
            }
        }
    }
}
'@
}

function Format-DemoProcessArgumentList {
    param([string[]]$ArgumentList)
    $parts = New-Object 'System.Collections.Generic.List[string]'
    foreach ($a in @($ArgumentList)) {
        if ($null -eq $a) { continue }
        $s = [string]$a
        if ($s -match '[\s"]') {
            $parts.Add('"' + ($s -replace '"', '\"') + '"') | Out-Null
        } else {
            $parts.Add($s) | Out-Null
        }
    }
    return [string]::Join(' ', @($parts.ToArray()))
}

function Start-DemoDetachedProcess {
    <#
      Starts a process with real stdout/stderr redirected to log files via inheritable
      Win32 handles (CreateProcess). Parent closes its copies immediately so the
      PowerShell host is not kept alive. Returns @{ Id = int }.
    #>
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$ArgumentList,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][string]$StdoutLog,
        [Parameter(Mandatory = $true)][string]$StderrLog
    )

    Ensure-DemoNativeStartType
    $argsText = Format-DemoProcessArgumentList -ArgumentList $ArgumentList
    $id = [DemoNativeStartV3]::Start(
        $FilePath,
        $argsText,
        $WorkingDirectory,
        $StdoutLog,
        $StderrLog
    )
    if ($id -le 0) {
        throw "Failed to start process: $FilePath"
    }
    return [pscustomobject]@{ Id = $id }
}

function Show-DemoLogTail {
    param(
        [string]$StdoutLog,
        [string]$StderrLog,
        [int]$Tail = 40
    )
    if (-not [string]::IsNullOrWhiteSpace($StdoutLog) -and (Test-Path -LiteralPath $StdoutLog)) {
        Write-Host ("----- tail {0} -----" -f ([IO.Path]::GetFileName($StdoutLog)))
        Get-Content -LiteralPath $StdoutLog -Tail $Tail -ErrorAction SilentlyContinue
    }
    if (-not [string]::IsNullOrWhiteSpace($StderrLog) -and (Test-Path -LiteralPath $StderrLog)) {
        Write-Host ("----- tail {0} -----" -f ([IO.Path]::GetFileName($StderrLog)))
        Get-Content -LiteralPath $StderrLog -Tail $Tail -ErrorAction SilentlyContinue
    }
}

function Get-DemoOwnedRecordsArray {
    <#
      Safe enumeration for System.Collections.Generic.List[object] on Windows PowerShell 5.1.
      Never use @($genericList) — it throws ArgumentException.
      Callers should wrap with @() to normalize empty/$null to a zero-length array.
    #>
    param($OwnedList)
    if ($null -eq $OwnedList) { return }
    if ($OwnedList.Count -le 0) { return }
    return @($OwnedList.ToArray())
}

function Stop-DemoProcessTreeByPid {
    <#
      taskkill /T on a previously validated launcher PID. Does not require WMI.
    #>
    param([int]$ProcessId)
    if ($ProcessId -le 0) { return $false }
    $taskkill = Join-Path $env:SystemRoot 'System32\taskkill.exe'
    if (-not (Test-Path -LiteralPath $taskkill)) {
        return $false
    }
    $p = Start-Process -FilePath $taskkill `
        -ArgumentList @('/PID', ([string]$ProcessId), '/T', '/F') `
        -WindowStyle Hidden `
        -Wait `
        -PassThru
    # 0 = success, 128 = process not found (already gone)
    return ($p.ExitCode -eq 0 -or $p.ExitCode -eq 128)
}

function Stop-DemoVerifiedLauncher {
    <#
      After PID+start+exe validation: taskkill /T first, then Stop-Process only on that
      launcher PID if still alive. Never used for inferred listeners or foreigners.
      Returns $true only when the launcher PID is gone afterward.
    #>
    param([int]$ProcessId)
    if ($ProcessId -le 0) { return $false }
    if (-not (Test-DemoProcessRunning -ProcessId $ProcessId)) { return $true }

    $null = Stop-DemoProcessTreeByPid -ProcessId $ProcessId
    Start-Sleep -Milliseconds 250
    if (-not (Test-DemoProcessRunning -ProcessId $ProcessId)) { return $true }

    try {
        Stop-Process -Id $ProcessId -Force -ErrorAction Stop
    } catch {
        Write-Warning ("Stop-Process fallback failed for PID {0}: {1}" -f $ProcessId, $_)
    }
    Start-Sleep -Milliseconds 250
    if (-not (Test-DemoProcessRunning -ProcessId $ProcessId)) { return $true }

    Write-Warning ("Verified launcher PID {0} is still running after taskkill and Stop-Process." -f $ProcessId)
    return $false
}

function Stop-DemoSessionOwnedRecords {
    <#
      Stops only session-owned launchers after handle re-validation.
      Does not use WMI. Does not kill arbitrary port listeners by inference.
    #>
    param(
        $OwnedList,
        [switch]$PassThru
    )
    $stopped = New-Object 'System.Collections.Generic.List[int]'
    $failed = $false
    $records = @(Get-DemoOwnedRecordsArray -OwnedList $OwnedList)
    foreach ($rec in $records) {
        $kind = [string]$rec.Kind
        if ($kind -notmatch '^launcher-') { continue }

        $handle = Get-DemoProcessHandleInfo -ProcessId ([int]$rec.Pid)
        if (-not $handle) { continue }
        if (-not (Test-SessionOwnedHandleMatch -HandleInfo $handle -Record $rec)) {
            Write-Warning ("Skipping PID {0}: handle identity no longer matches owned {1} metadata (left intact)." -f $rec.Pid, $kind)
            continue
        }
        try {
            $ok = Stop-DemoVerifiedLauncher -ProcessId ([int]$handle.Pid)
            if ($ok) {
                Write-Host ("Stopped owned PID {0} ({1})" -f $handle.Pid, $kind)
                $stopped.Add([int]$handle.Pid) | Out-Null
            } else {
                $failed = $true
                Write-Warning "Failed to stop owned PID $($handle.Pid)"
            }
        } catch {
            $failed = $true
            Write-Warning "Could not stop owned PID $($rec.Pid): $_"
        }
    }
    if ($PassThru) {
        return [pscustomobject]@{
            StoppedPids = @($stopped.ToArray())
            Failed      = $failed
        }
    }
}

function Clear-DemoSessionArtifacts {
    <#
      Deletes only allowed direct-child files of PidDir (GetFullPath containment).
      Removes $PidDir only when it exists and is empty afterward. Never -Recurse wipe.
    #>
    param(
        [string[]]$ArtifactPaths,
        [string]$PidDir
    )
    if ([string]::IsNullOrWhiteSpace($PidDir)) { return }

    $pidFull = $null
    try {
        $pidFull = [System.IO.Path]::GetFullPath($PidDir)
    } catch {
        Write-Warning ("Invalid PidDir (not cleaned): {0}" -f $PidDir)
        return
    }

    foreach ($path in @($ArtifactPaths)) {
        if ([string]::IsNullOrWhiteSpace($path)) { continue }
        if (-not (Test-DemoArtifactPathAllowed -ArtifactPath $path -PidDir $pidFull)) {
            Write-Warning ("Refusing to delete artifact outside PidDir or invalid path (left intact): {0}" -f $path)
            continue
        }
        $artFull = [System.IO.Path]::GetFullPath($path)
        if (-not (Test-Path -LiteralPath $artFull)) { continue }
        try {
            $item = Get-Item -LiteralPath $artFull -Force -ErrorAction Stop
            if ($item.PSIsContainer) {
                Write-Warning ("Refusing to delete directory artifact (left intact): {0}" -f $artFull)
                continue
            }
            Remove-Item -LiteralPath $artFull -Force -ErrorAction Stop
        } catch {
            Write-Warning "Could not remove session artifact ${artFull}: $_"
        }
    }

    if (-not (Test-Path -LiteralPath $pidFull)) { return }
    $remaining = @(Get-ChildItem -LiteralPath $pidFull -Force -ErrorAction SilentlyContinue)
    if ($remaining.Count -eq 0) {
        try {
            Remove-Item -LiteralPath $pidFull -Force -ErrorAction Stop
        } catch {
            Write-Warning "Could not remove empty PidDir ${pidFull}: $_"
        }
    }
}
