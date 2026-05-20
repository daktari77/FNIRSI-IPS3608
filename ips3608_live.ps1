param(
    [string]$PortName = "COM13",
    [int]$BaudRate = 9600,
    [int]$IntervalMs = 500,
    [int]$Count = 20
)

$ErrorActionPreference = "Stop"

function New-Command {
    param(
        [byte]$CmdType,
        [byte]$Register,
        [byte[]]$Data
    )
    $len = [byte]$Data.Length
    $sum = [int]$Register + [int]$len
    foreach ($b in $Data) { $sum += [int]$b }
    $checksum = [byte]($sum -band 0xFF)

    $packet = New-Object byte[] (5 + $Data.Length)
    $packet[0] = 0xF1
    $packet[1] = $CmdType
    $packet[2] = $Register
    $packet[3] = $len
    for ($i = 0; $i -lt $Data.Length; $i++) {
        $packet[4 + $i] = $Data[$i]
    }
    $packet[4 + $Data.Length] = $checksum
    return $packet
}

function Read-Frames {
    param(
        [System.IO.Ports.SerialPort]$Port,
        [int]$TimeoutMs = 700
    )

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $buf = New-Object System.Collections.Generic.List[byte]
    $frames = New-Object System.Collections.Generic.List[byte[]]

    while ($sw.ElapsedMilliseconds -lt $TimeoutMs) {
        $n = $Port.BytesToRead
        if ($n -gt 0) {
            $tmp = New-Object byte[] $n
            [void]$Port.Read($tmp, 0, $n)
            $buf.AddRange($tmp)

            $progress = $true
            while ($progress) {
                $progress = $false

                if ($buf.Count -lt 5) {
                    break
                }

                while ($buf.Count -gt 0 -and $buf[0] -ne 0xF0) {
                    $buf.RemoveAt(0)
                }

                if ($buf.Count -lt 5) {
                    break
                }

                $len = [int]$buf[3]
                $frameLen = 5 + $len

                if ($buf.Count -lt $frameLen) {
                    break
                }

                $frame = New-Object byte[] $frameLen
                for ($i = 0; $i -lt $frameLen; $i++) {
                    $frame[$i] = $buf[$i]
                }
                $frames.Add($frame)
                $buf.RemoveRange(0, $frameLen)
                $progress = $true
            }
        }
        Start-Sleep -Milliseconds 20
    }

    return $frames
}

function Get-FloatLE {
    param([byte[]]$Bytes, [int]$Offset)
    return [Math]::Round([BitConverter]::ToSingle($Bytes, $Offset), 4)
}

$cmdConnect = New-Command -CmdType 0xC1 -Register 0x00 -Data ([byte[]](0x01))
$cmdReadLive = New-Command -CmdType 0xA1 -Register 0xC3 -Data ([byte[]](0x00))
$cmdReadTemp = New-Command -CmdType 0xA1 -Register 0xC4 -Data ([byte[]](0x00))
$cmdDisconnect = New-Command -CmdType 0xC1 -Register 0x00 -Data ([byte[]](0x00))

$port = New-Object System.IO.Ports.SerialPort $PortName, $BaudRate, 'None', 8, 'one'
$port.ReadTimeout = 200
$port.WriteTimeout = 1000
$port.Handshake = 'None'
$port.DtrEnable = $true
$port.RtsEnable = $true

try {
    $port.Open()
    Start-Sleep -Milliseconds 200
    $port.DiscardInBuffer()
    $port.DiscardOutBuffer()

    $port.Write($cmdConnect, 0, $cmdConnect.Length)
    [void](Read-Frames -Port $port -TimeoutMs 600)

    Write-Host ("Connected to {0} @ {1}" -f $PortName, $BaudRate)
    Write-Host "Time                 Voltage(V)  Current(A)  Power(W)  Temp(C)"
    Write-Host "-------------------------------------------------------------"

    $i = 0
    while ($Count -le 0 -or $i -lt $Count) {
        $i++
        $v = $null
        $a = $null
        $w = $null
        $t = $null

        $port.Write($cmdReadLive, 0, $cmdReadLive.Length)
        $frames = Read-Frames -Port $port -TimeoutMs 500
        foreach ($f in $frames) {
            if ($f.Length -ge 17 -and $f[1] -eq 0xA1 -and $f[2] -eq 0xC3 -and $f[3] -eq 0x0C) {
                $payload = $f[4..15]
                $v = Get-FloatLE -Bytes $payload -Offset 0
                $a = Get-FloatLE -Bytes $payload -Offset 4
                $w = Get-FloatLE -Bytes $payload -Offset 8
            }
        }

        $port.Write($cmdReadTemp, 0, $cmdReadTemp.Length)
        $frames = Read-Frames -Port $port -TimeoutMs 350
        foreach ($f in $frames) {
            if ($f.Length -ge 9 -and $f[1] -eq 0xA1 -and $f[2] -eq 0xC4 -and $f[3] -eq 0x04) {
                $payload = $f[4..7]
                $t = Get-FloatLE -Bytes $payload -Offset 0
            }
        }

        $ts = (Get-Date).ToString("HH:mm:ss")
        $sv = if ($null -ne $v) { "{0,9:N3}" -f $v } else { "    n/a  " }
        $sa = if ($null -ne $a) { "{0,9:N3}" -f $a } else { "    n/a  " }
        $sw = if ($null -ne $w) { "{0,8:N3}" -f $w } else { "   n/a  " }
        $st = if ($null -ne $t) { "{0,7:N1}" -f $t } else { "  n/a " }

        Write-Host ("{0}   {1}   {2}   {3}   {4}" -f $ts, $sv, $sa, $sw, $st)
        Start-Sleep -Milliseconds $IntervalMs
    }
}
finally {
    try {
        if ($port -and $port.IsOpen) {
            $port.Write($cmdDisconnect, 0, $cmdDisconnect.Length)
            Start-Sleep -Milliseconds 80
            $port.Close()
        }
    }
    catch {}
    if ($port) { $port.Dispose() }
}
