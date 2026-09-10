from __future__ import annotations

import os, platform, queue, subprocess, sys, tempfile, threading, time, traceback
from datetime import datetime
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageOps

from . import __version__
from .editor import MaskEditor
from .engine import ProcessResult, output_path_for
from .ui import BackgroundPXRApp

TXT={
"English":{"log":"LOG","window":"BackgroundPXR — Diagnostics & Error Log","title":"DIAGNOSTICS & ERROR LOG","sub":"Live processing history and full technical errors","copy":"Copy report","open":"Open logs folder","clear":"Clear log","close":"Close","copied":"Report copied to clipboard.","cleared":"Log cleared.","open_img":"Opening image","ai":"AI removal / model","refine":"Refining edges","compose":"Building result","save":"Saving file","done":"Completed","cancel_wait":"Cancelling after current AI step","ready_result":"AI result ready","finished":"Finished","cancelled":"Cancelled","errors":"errors","ok":"ok","error":"ERROR","idle":"Ready — diagnostics active"},
"Polski":{"log":"LOG","window":"BackgroundPXR — Diagnostyka i dziennik błędów","title":"DIAGNOSTYKA I DZIENNIK BŁĘDÓW","sub":"Historia pracy na żywo i pełne informacje techniczne","copy":"Kopiuj raport","open":"Otwórz folder logów","clear":"Wyczyść log","close":"Zamknij","copied":"Raport skopiowany do schowka.","cleared":"Dziennik wyczyszczony.","open_img":"Otwieranie zdjęcia","ai":"Usuwanie tła AI / model","refine":"Dopracowanie krawędzi","compose":"Tworzenie wyniku","save":"Zapisywanie pliku","done":"Gotowe","cancel_wait":"Anulowanie po zakończeniu kroku AI","ready_result":"Wynik AI gotowy","finished":"Zakończono","cancelled":"Anulowano","errors":"błędów","ok":"OK","error":"BŁĄD","idle":"Gotowy — diagnostyka aktywna"}}

def tx(lang,key): return TXT.get(lang,TXT["English"]).get(key,key)

class DiagnosticsStore:
    def __init__(self,directory=None):
        if directory is None:
            base=Path(os.environ.get("LOCALAPPDATA",Path.home()/".backgroundpxr")); directory=base/"BackgroundPXR"/"logs"
        self.directory=Path(directory)
        try: self.directory.mkdir(parents=True,exist_ok=True)
        except OSError:
            self.directory=Path(tempfile.gettempdir())/"BackgroundPXR"/"logs"; self.directory.mkdir(parents=True,exist_ok=True)
        self.path=self.directory/"backgroundpxr.log"; self.backup=self.directory/"backgroundpxr.log.1"; self.lock=threading.Lock(); self.lines=[]
        self.write("INFO","session",f"BackgroundPXR {__version__} started | Python {sys.version.split()[0]} | {platform.platform()}")
    def _rotate(self):
        try:
            if self.path.exists() and self.path.stat().st_size>2_000_000:
                if self.backup.exists(): self.backup.unlink()
                self.path.replace(self.backup)
        except OSError: pass
    def write(self,level,stage,message,file_name=None,error_id=None,trace=None):
        bits=[f"[{datetime.now():%Y-%m-%d %H:%M:%S}]",level.upper(),stage]
        if error_id: bits.append(error_id)
        if file_name: bits.append(str(file_name))
        line=" | ".join(bits)+" | "+str(message).replace("\n"," ").strip(); block=line+("\n"+trace.rstrip() if trace else "")+"\n"
        with self.lock:
            self.lines.append(block.rstrip()); self.lines=self.lines[-1200:]
            try:
                self._rotate()
                with self.path.open("a",encoding="utf-8") as f: f.write(block)
            except OSError: pass
    def exception(self,stage,file_name,exc,trace):
        eid="PXR-"+datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:-3]; self.write("ERROR",stage,f"{type(exc).__name__}: {exc}",file_name,eid,trace); return eid
    def report(self,max_chars=120000):
        with self.lock: text="\n".join(self.lines)
        if not text:
            try: text=self.path.read_text(encoding="utf-8")
            except OSError: text=""
        return text[-max_chars:]
    def clear(self):
        with self.lock:
            self.lines.clear()
            try: self.path.write_text("",encoding="utf-8")
            except OSError: pass

class BackgroundPXRDiagnosticsApp(BackgroundPXRApp):
    """Studio UI plus live percentage, heartbeat and persistent error diagnostics."""
    def __init__(self,root):
        self.diagnostics=DiagnosticsStore(); self._diag_window=self._diag_textbox=self._diag_summary=None; self._diag_percent_var=self._diag_button=None
        self._diag_error_count=0; self._diag_current_percent=0; self._diag_run_started=0.0
        super().__init__(root); self._attach_diag(); self.diagnostics.write("INFO","ui","Diagnostics UI attached and ready")
    def _apply_language(self):
        super()._apply_language()
        if self._diag_button is not None: self._diag_lang()
    def _attach_diag(self):
        card=self.progress_bar.master; self._diag_percent_var=ctk.StringVar(value="0%")
        self.progress_bar.grid_configure(padx=(10,55),pady=(8,2))
        self._diag_percent_label=ctk.CTkLabel(card,textvariable=self._diag_percent_var,width=42,height=16,font=ctk.CTkFont("Segoe UI",8,"bold"),text_color=self.ACCENT); self._diag_percent_label.grid(row=4,column=0,sticky="e",padx=10,pady=(3,0))
        self.status_label.grid_configure(padx=(10,68),pady=(0,1)); self.status_label.bind("<Button-1>",lambda _e:self._open_diag())
        self._diag_button=ctk.CTkButton(card,text="LOG",command=self._open_diag,width=54,height=21,fg_color="#102B49",hover_color="#18466F",border_width=1,border_color="#28557D",font=ctk.CTkFont("Segoe UI",7,"bold")); self._diag_button.grid(row=5,column=0,sticky="e",padx=10,pady=(0,1))
        self.status_text.set(tx(self.language.get(),"idle")); self._diag_lang()
    def _diag_lang(self):
        if self._diag_button is not None: self._diag_button.configure(text=tx(self.language.get(),"log")+(f" {self._diag_error_count}" if self._diag_error_count else ""))
        if self._diag_window is not None and self._diag_window.winfo_exists(): self._diag_window.title(tx(self.language.get(),"window")); self._refresh_diag()
    def _diag_button_state(self,error=False):
        if self._diag_button is None: return
        self._diag_button.configure(fg_color=self.DANGER if error else "#102B49",hover_color="#B53D58" if error else "#18466F",border_color="#FF8EA4" if error else "#28557D"); self._diag_lang()
    def _open_diag(self):
        if self._diag_window is not None:
            try:
                if self._diag_window.winfo_exists(): self._diag_window.deiconify(); self._diag_window.lift(); self._refresh_diag(); return
            except Exception: pass
        t=ctk.CTkToplevel(self.root); self._diag_window=t; t.title(tx(self.language.get(),"window")); t.geometry("860x560"); t.minsize(680,420); t.configure(fg_color="#06101E"); t.grid_rowconfigure(2,weight=1); t.grid_columnconfigure(0,weight=1)
        h=ctk.CTkFrame(t,corner_radius=0,fg_color="#08172A",height=72); h.grid(row=0,column=0,sticky="ew"); h.grid_propagate(False); h.grid_columnconfigure(0,weight=1)
        self._diag_title=ctk.CTkLabel(h,text="",font=ctk.CTkFont("Segoe UI",17,"bold"),text_color=self.TEXT); self._diag_title.grid(row=0,column=0,sticky="w",padx=18,pady=(11,0))
        self._diag_sub=ctk.CTkLabel(h,text="",font=ctk.CTkFont("Segoe UI",9),text_color=self.MUTED); self._diag_sub.grid(row=1,column=0,sticky="w",padx=18,pady=(0,8))
        self._diag_summary=ctk.CTkLabel(t,text="",anchor="w",height=32,corner_radius=8,fg_color="#0B2139",text_color="#A9D8FF",font=ctk.CTkFont("Segoe UI",9,"bold")); self._diag_summary.grid(row=1,column=0,sticky="ew",padx=14,pady=(10,6))
        self._diag_textbox=ctk.CTkTextbox(t,corner_radius=10,fg_color="#050D18",border_width=1,border_color="#1A4062",text_color="#C9D8E8",font=ctk.CTkFont("Consolas",10),wrap="word"); self._diag_textbox.grid(row=2,column=0,sticky="nsew",padx=14,pady=(0,8))
        b=ctk.CTkFrame(t,fg_color="transparent"); b.grid(row=3,column=0,sticky="ew",padx=14,pady=(0,12)); b.grid_columnconfigure(3,weight=1)
        self._diag_copy=ctk.CTkButton(b,text="",command=self._copy_diag,height=32,fg_color=self.VIOLET); self._diag_copy.grid(row=0,column=0,padx=(0,6))
        self._diag_open=ctk.CTkButton(b,text="",command=self._open_log_folder,height=32,fg_color="#12304E"); self._diag_open.grid(row=0,column=1,padx=6)
        self._diag_clear=ctk.CTkButton(b,text="",command=self._clear_diag,height=32,fg_color="#47283A",hover_color="#643247"); self._diag_clear.grid(row=0,column=2,padx=6)
        self._diag_close=ctk.CTkButton(b,text="",command=t.withdraw,height=32,width=86,fg_color="#102B49"); self._diag_close.grid(row=0,column=4,padx=(6,0)); self._refresh_diag()
    def _refresh_diag(self):
        if self._diag_window is None or not self._diag_window.winfo_exists(): return
        L=self.language.get(); self._diag_title.configure(text=tx(L,"title")); self._diag_sub.configure(text=tx(L,"sub")); self._diag_copy.configure(text=tx(L,"copy")); self._diag_open.configure(text=tx(L,"open")); self._diag_clear.configure(text=tx(L,"clear")); self._diag_close.configure(text=tx(L,"close"))
        self._diag_summary.configure(text=f"  {self._diag_current_percent}%   •   {tx(L,'errors')}: {self._diag_error_count}   •   {self.diagnostics.path}")
        r=self.diagnostics.report(); self._diag_textbox.configure(state="normal"); self._diag_textbox.delete("1.0","end"); self._diag_textbox.insert("1.0",r or tx(L,"idle")); self._diag_textbox.see("end"); self._diag_textbox.configure(state="disabled")
    def _copy_diag(self):
        self.root.clipboard_clear(); self.root.clipboard_append(self.diagnostics.report()); self.status_text.set(tx(self.language.get(),"copied"))
    def _clear_diag(self):
        self.diagnostics.clear(); self._diag_error_count=0; self._diag_button_state(False); self.status_text.set(tx(self.language.get(),"cleared")); self._refresh_diag()
    def _open_log_folder(self):
        try:
            self.diagnostics.directory.mkdir(parents=True,exist_ok=True)
            if os.name=="nt": os.startfile(self.diagnostics.directory)  # type: ignore[attr-defined]
            else: subprocess.Popen(["xdg-open",str(self.diagnostics.directory)])
        except Exception as exc:
            eid=self.diagnostics.exception("open-log-folder",self.diagnostics.directory,exc,traceback.format_exc()); self._error_status(eid,self.diagnostics.directory.name,type(exc).__name__)
    def _live(self,overall,stage,pos,total,name,elapsed=None):
        overall=max(0.0,min(1.0,float(overall))); pct=int(round(overall*100)); self._diag_current_percent=pct; self.progress.set(overall)
        if self._diag_percent_var is not None: self._diag_percent_var.set(f"{pct}%")
        self.status_text.set(f"{pct}% • {tx(self.language.get(),stage)} • {pos}/{total} • {name}"+(f" • {elapsed}s" if elapsed is not None else "")); self.status_label.configure(text_color=self.ACCENT); self._diag_percent_label.configure(text_color=self.ACCENT); self._refresh_diag()
    def _error_status(self,eid,name,etype):
        self._diag_error_count+=1; self.status_text.set(f"{tx(self.language.get(),'error')} {eid} • {name} • {etype}"); self.status_label.configure(text_color="#FF8EA4"); self._diag_percent_label.configure(text_color="#FF8EA4"); self._diag_button_state(True); self._refresh_diag()
    @staticmethod
    def _overall(pos,total,local): return 0.0 if total<=0 else ((pos-1)+max(0.0,min(1.0,local)))/total
    def _emit(self,pos,total,name,local,stage,elapsed=None): self.events.put(("diag_stage",self._overall(pos,total,local),stage,pos,total,name,elapsed))
    def _start_worker(self,indices,save):
        if self.worker and self.worker.is_alive(): self.cancel_event.set(); self.status_text.set(tx(self.language.get(),"cancel_wait")); self.diagnostics.write("WARN","cancel","Cancellation requested by user"); return
        self._diag_error_count=0; self._diag_current_percent=0; self._diag_run_started=time.monotonic(); self._diag_button_state(False); self._diag_percent_var.set("0%"); self.diagnostics.write("INFO","run",f"Run started | items={len(indices)} | save={bool(save)} | model={self.model.get()}"); super()._start_worker(indices,save)
    def _worker(self,items,opts,save):
        ok=fail=0; total=len(items)
        for pos,(idx,path) in enumerate(items,1):
            if self.cancel_event.is_set(): break
            name=path.name; self._emit(pos,total,name,.03,"open_img"); self.diagnostics.write("INFO","open","Opening source image",str(path))
            try:
                with Image.open(path) as src: original=ImageOps.exif_transpose(src).convert("RGBA")
                self._emit(pos,total,name,.16,"ai"); self.diagnostics.write("INFO","ai",f"AI removal started | model={opts.model_label} | alpha_matting={opts.alpha_matting}",str(path))
                stop=threading.Event(); started=time.monotonic()
                def heartbeat():
                    while not stop.wait(1.0): self._emit(pos,total,name,.16,"cancel_wait" if self.cancel_event.is_set() else "ai",int(time.monotonic()-started))
                threading.Thread(target=heartbeat,daemon=True).start()
                try: ai=self.engine.remove_background(original,opts)
                finally: stop.set()
                if self.cancel_event.is_set(): break
                self._emit(pos,total,name,.74,"refine"); cutout=self.engine.refine_cutout(original,ai,opts)
                self._emit(pos,total,name,.84,"compose"); output=self.engine.compose(original,cutout,opts); result=ProcessResult(original,cutout,output); dest=None
                if save:
                    self._emit(pos,total,name,.92,"save"); dest=output_path_for(path,self.output_dir.get(),opts.export_format,opts.output_suffix); self.engine.save(output,dest,opts.export_format)
                ok+=1; self.diagnostics.write("INFO","complete",f"Item completed | output={dest if dest else 'preview only'}",str(path)); self.events.put(("result",idx,result,str(dest) if dest else None)); self._emit(pos,total,name,1.0,"done")
            except Exception as exc:
                fail+=1; trace=traceback.format_exc(); eid=self.diagnostics.exception("processing",path,exc,trace); self.events.put(("diag_error",pos,total,name,eid,type(exc).__name__,str(exc))); self.events.put(("progress",pos/total if total else 0.0))
        self.events.put(("done",ok,fail,self.cancel_event.is_set(),save))
    def _poll_events(self):
        try:
            while True:
                e=self.events.get_nowait(); k=e[0]; L=self.language.get()
                if k=="diag_stage": _,o,s,p,t,n,elapsed=e; self._live(o,s,p,t,n,elapsed)
                elif k=="progress": self.progress.set(float(e[1]))
                elif k=="result":
                    _,idx,res,dest=e
                    if idx==self.selected_index: self.current_result=res; self.editor=MaskEditor(res.original,res.cutout); self.preview_after=res.output; self._set_tool("pan")
                    if dest: self.diagnostics.write("INFO","saved",f"Saved: {dest}")
                elif k=="diag_error":
                    _,p,t,n,eid,etype,msg=e; self._diag_current_percent=int(round((p/t)*100)) if t else self._diag_current_percent; self._diag_percent_var.set(f"{self._diag_current_percent}%"); self._error_status(eid,n,etype); self.diagnostics.write("INFO","ui-error",f"Displayed error to user: {msg}",error_id=eid)
                    if t==1: self._open_diag()
                elif k=="done":
                    _,ok,fail,cancelled,save=e; self.remove_btn.configure(state="normal"); self.process_all_btn.configure(text=self._tr_process_all(),fg_color="#12304E"); elapsed=max(0,int(time.monotonic()-self._diag_run_started))
                    if cancelled: self.status_text.set(f"{self._diag_current_percent}% • {tx(L,'cancelled')} • {elapsed}s"); self.diagnostics.write("WARN","run",f"Run cancelled after {elapsed}s | ok={ok} | fail={fail}")
                    else:
                        self._diag_current_percent=100; self.progress.set(1.0); self._diag_percent_var.set("100%"); self.status_text.set(f"100% • {tx(L,'finished')} • {ok} {tx(L,'ok')} • {fail} {tx(L,'errors')} • {elapsed}s" if save else f"100% • {tx(L,'ready_result')} • {elapsed}s"); self.status_label.configure(text_color=self.GREEN if not fail else "#FF8EA4"); self.diagnostics.write("INFO","run",f"Run finished after {elapsed}s | ok={ok} | fail={fail} | save={save}")
                    if save and not cancelled and ok and self.auto_open_output.get(): self._open_output_folder()
                    self._refresh_diag()
                elif k=="status": _,p,t,n=e; self._live(self._overall(p,t,.05),"open_img",p,t,n)
                elif k=="error": _,n,msg=e; exc=RuntimeError(msg); eid=self.diagnostics.exception("legacy-processing",n,exc,msg); self._error_status(eid,n,type(exc).__name__)
        except queue.Empty: pass
        except Exception as exc:
            eid=self.diagnostics.exception("event-loop","UI",exc,traceback.format_exc()); self._error_status(eid,"UI",type(exc).__name__)
        self.root.after(80,self._poll_events)
    def _tr_process_all(self):
        try:
            from .i18n import tr
            return tr(self.language.get(),"process_all")
        except Exception: return "Process All" if self.language.get()=="English" else "Przetwórz wszystkie"
    def _recompose(self):
        if not self.editor: return
        try: self.preview_after=self.engine.compose(self.editor.original,self.editor.current_cutout(),self._options())
        except Exception as exc:
            name=self.files[self.selected_index].name if self.selected_index is not None and self.selected_index<len(self.files) else "preview"; eid=self.diagnostics.exception("compose",name,exc,traceback.format_exc()); self._error_status(eid,name,type(exc).__name__)
    def _export_current(self):
        try: return super()._export_current()
        except Exception as exc:
            name=self.files[self.selected_index].name if self.selected_index is not None and self.selected_index<len(self.files) else "export"; eid=self.diagnostics.exception("export",name,exc,traceback.format_exc()); self._error_status(eid,name,type(exc).__name__); self._open_diag()
    def _on_close(self): self.diagnostics.write("INFO","session","Application closed"); super()._on_close()
