param(
    [Parameter(Mandatory=$true)][string]$Archive,
    [Parameter(Mandatory=$true)][ValidatePattern('^https://')][string]$SourceUrl
)
# Maintenance-only: ask Windows attachment services to CHECK a disposable copy.
# Never calls Execute/Prompt/ClearClientState, never changes protection settings.
# GUIDs and vtable order: Windows SDK shobjidl_core.h / shobjidl.h.
$ErrorActionPreference = 'Stop'
$attachmentResult = @{ status='fail'; method='IAttachmentExecute.Save'; source_url=$SourceUrl }
$attachmentWork = $null
$attachmentStage = 'read-protection-preferences'
try {
    $attachmentPreference = Get-MpPreference -ErrorAction Stop
    $attachmentStage = 'read-protection-status'
    $attachmentStatus = Get-MpComputerStatus -ErrorAction Stop
    if ($attachmentPreference.DisableIOAVProtection -or $attachmentPreference.DisableRealtimeMonitoring -or -not $attachmentStatus.RealTimeProtectionEnabled) {
        throw 'Real-time and downloaded-attachment protection must be enabled'
    }
    $attachmentStage = 'resolve-input'
    $attachmentInput = (Resolve-Path -LiteralPath $Archive -ErrorAction Stop).Path
    $attachmentStage = 'hash-input'
    $attachmentHash = (Get-FileHash -LiteralPath $attachmentInput -Algorithm SHA256).Hash.ToLowerInvariant()
    $attachmentResult.archive_sha256 = $attachmentHash
    $attachmentWork = Join-Path ([IO.Path]::GetTempPath()) ('taiwan-exam-attachment-' + [Guid]::NewGuid().ToString('N'))
    [IO.Directory]::CreateDirectory($attachmentWork) | Out-Null
    $attachmentCopy = Join-Path $attachmentWork ([IO.Path]::GetFileName($attachmentInput))
    $attachmentStage = 'copy-input'
    Copy-Item -LiteralPath $attachmentInput -Destination $attachmentCopy -ErrorAction Stop
    $attachmentStage = 'load-attachment-api'
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
namespace TaiwanExamSecurity {
    [ComImport, Guid("73db1241-1e85-4581-8e4f-a81e1d0f8c57"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    public interface IAttachmentCheck {
        [PreserveSig] int SetClientTitle([MarshalAs(UnmanagedType.LPWStr)] string title);
        [PreserveSig] int SetClientGuid(ref Guid client);
        [PreserveSig] int SetLocalPath([MarshalAs(UnmanagedType.LPWStr)] string path);
        [PreserveSig] int SetFileName([MarshalAs(UnmanagedType.LPWStr)] string name);
        [PreserveSig] int SetSource([MarshalAs(UnmanagedType.LPWStr)] string source);
        [PreserveSig] int SetReferrer([MarshalAs(UnmanagedType.LPWStr)] string source);
        [PreserveSig] int CheckPolicy();
        [PreserveSig] int Prompt(IntPtr owner, int prompt, out int action);
        [PreserveSig] int Save();
    }
    public static class AttachmentCheck {
        public static int Check(string path, string source) {
            var service = (IAttachmentCheck)Activator.CreateInstance(Type.GetTypeFromCLSID(new Guid("4125dd96-e03a-4103-8f70-e0597d803b9c")));
            try {
                var client = new Guid("a1d8775a-f544-4e0a-96d2-a72a4c36ac99");
                Marshal.ThrowExceptionForHR(service.SetClientGuid(ref client));
                Marshal.ThrowExceptionForHR(service.SetLocalPath(path));
                Marshal.ThrowExceptionForHR(service.SetSource(source));
                return service.Save();
            } finally { Marshal.ReleaseComObject(service); }
        }
    }
}
'@
    $attachmentStage = 'attachment-save'
    $attachmentReturn = [TaiwanExamSecurity.AttachmentCheck]::Check($attachmentCopy, $SourceUrl)
    $attachmentResult.hresult = $attachmentReturn
    $attachmentResult.hresult_hex = '0x' + $attachmentReturn.ToString('X8')
    if ($attachmentReturn -ne 0) { throw 'Attachment services rejected the candidate' }
    if ((Get-FileHash -LiteralPath $attachmentCopy -Algorithm SHA256).Hash.ToLowerInvariant() -ne $attachmentHash) {
        throw 'Checked copy was changed or removed'
    }
    if ((Get-FileHash -LiteralPath $attachmentInput -Algorithm SHA256).Hash.ToLowerInvariant() -ne $attachmentHash) {
        throw 'Original archive changed during check'
    }
    $attachmentResult.status = 'pass'
} catch {
    $attachmentResult.stage = $attachmentStage
    if ($_.Exception -is [System.Management.Automation.CommandNotFoundException]) {
        $attachmentResult.missing_command = $_.Exception.CommandName
    }
    $attachmentResult.error = 'Attachment check failed; do not release (no automatic retry or protection bypass)'
    if (-not $attachmentResult.ContainsKey('hresult')) {
        $attachmentResult.error_type = $_.Exception.GetType().FullName
    }
} finally {
    if ($attachmentWork -and [IO.Directory]::Exists($attachmentWork)) {
        # Only the explicitly created test file; no recursive deletion.
        if ($attachmentCopy -and [IO.File]::Exists($attachmentCopy)) { Remove-Item -LiteralPath $attachmentCopy -Force }
        if (@(Get-ChildItem -LiteralPath $attachmentWork -Force).Count -eq 0) { [IO.Directory]::Delete($attachmentWork) }
    }
}
$attachmentResult | ConvertTo-Json -Compress
if ($attachmentResult.status -ne 'pass') { exit 2 }
