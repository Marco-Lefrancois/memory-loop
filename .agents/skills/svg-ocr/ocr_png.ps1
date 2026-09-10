<#
.SYNOPSIS
  OCR de fichiers image (PNG/JPG) via le moteur natif Windows (Windows.Media.Ocr).
  Aucune dépendance externe (Tesseract, cloud) — utilise l'API WinRT présente dans System32.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File ocr_png.ps1 -Files "C:\a.png,C:\b.png"
  powershell -NoProfile -ExecutionPolicy Bypass -File ocr_png.ps1 -Files "C:\a.png" -Language "fr-CA"

.NOTES
  Sortie : texte reconnu ligne par ligne, précédé d'un séparateur par fichier.
  Les accents peuvent être mal encodés par l'OCR — traiter comme transcription indicative.
#>
param(
    [Parameter(Mandatory = $true)][string]$Files,
    [string]$Language = ""
)

Add-Type -AssemblyName System.Runtime.WindowsRuntime

$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
        $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and `
            $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
    })[0]

function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}

[Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null
[Windows.Storage.StorageFile, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null
[Windows.Globalization.Language, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null

if ($Language -ne "") {
    $lang = [Windows.Globalization.Language]::new($Language)
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
    if ($null -eq $engine) {
        Write-Warning "Pack de langue '$Language' indisponible. Fallback sur la langue du profil."
        $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
    }
}
else {
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
}

if ($null -eq $engine) {
    Write-Error "Impossible de créer un moteur OCR (aucun pack de langue OCR installé)."
    exit 1
}

foreach ($f in ($Files -split ',')) {
    $f = $f.Trim()
    if (-not (Test-Path -LiteralPath $f)) {
        Write-Warning "Fichier introuvable : $f"
        continue
    }
    Write-Output "==================== $([System.IO.Path]::GetFileName($f)) ===================="
    $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($f)) ([Windows.Storage.StorageFile])
    $stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
    $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
    $bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
    $result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
    foreach ($line in $result.Lines) {
        Write-Output $line.Text
    }
    $stream.Dispose()
}
