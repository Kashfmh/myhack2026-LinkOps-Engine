import time
import random
import concurrent.futures
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from config import MAX_FILES, MAX_FILE_SIZE_MB
from ui.dialogs import preview_dialog


class DummyFile:
    # wraps a file dict so it looks like an UploadedFile to the API
    def __init__(self, f_dict):
        self.name  = f_dict['name']
        self.type  = f_dict['type']
        self.bytes = f_dict['bytes']

    def getvalue(self):
        return self.bytes


def render_file_manager(execute_match_protocol_fn, mentors_df: pd.DataFrame,
                        partners_df: pd.DataFrame):
    st.markdown('<h1 style="font-size: 2.5rem; margin-bottom: 0;">LinkOps Engine</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #8b949e; font-size: 1.1rem; margin-top: 0;">Automated Linkage Engine for Program Administrators</p>', unsafe_allow_html=True)
    st.write("")

    # file uploader
    uploaded_new = st.file_uploader(
        "Drop Startup Pitch Decks (PDF/Images) here for bulk processing",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key=f"uploader_{st.session_state.uploader_key}"
    )

    if uploaded_new:
        added = False
        for f in uploaded_new:
            if len(st.session_state.file_manager) >= MAX_FILES:
                st.session_state.toast_msg  = f"Maximum {MAX_FILES} files allowed."
                st.session_state.toast_type = "error"
                break

            if f.size > MAX_FILE_SIZE_MB * 1024 * 1024:
                st.session_state.toast_msg  = f"'{f.name}' exceeds the {MAX_FILE_SIZE_MB}MB limit."
                st.session_state.toast_type = "error"
                continue

            # prevent dupes
            if not any(existing['name'] == f.name for existing in st.session_state.file_manager):
                st.session_state.file_manager.append({
                    "name":  f.name,
                    "type":  f.type,
                    "size":  f.size,
                    "bytes": f.getvalue()
                })
                added = True

        if added:
            st.session_state.uploader_key += 1
            st.session_state.toast_msg  = "Files uploaded successfully!"
            st.session_state.toast_type = "success"
            st.rerun()

    # file list ui
    if st.session_state.file_manager:
        st.markdown('<div style="margin-top: 1rem; margin-bottom: 0.5rem; font-weight: 600; color: #8b949e; text-transform: uppercase; font-size: 0.85em;">Ready for Processing:</div>', unsafe_allow_html=True)

        for idx, f in enumerate(st.session_state.file_manager):
            is_analysed = f['name'] in st.session_state.processed_startups
            with st.container(border=True):
                col_icon, col_name, col_status, col_size, col_eye, col_x = st.columns(
                    [0.5, 6, 2, 2, 0.7, 0.7], vertical_alignment="center"
                )

                with col_icon:
                    icon = "picture_as_pdf" if f['type'] == "application/pdf" else "image"
                    st.markdown(f'<span class="material-symbols-outlined" style="color: #8b949e;">{icon}</span>', unsafe_allow_html=True)

                with col_name:
                    st.markdown(f"<span style='color:#e6edf3; font-weight: 500;'>{f['name']}</span>", unsafe_allow_html=True)

                with col_status:
                    if is_analysed:
                        st.markdown(
                            '<span style="background:rgba(16,185,129,0.1); color:#10b981; border:1px solid #10b981; '
                            'border-radius:999px; padding:2px 10px; font-size:11px; font-weight:600; '
                            'display:inline-flex; align-items:center; gap:4px;">'
                            '<span class="material-symbols-outlined" style="font-size:13px;">check_circle</span>'
                            'Analysed</span>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            '<span style="background:rgba(245,158,11,0.1); color:#f59e0b; border:1px solid #f59e0b; '
                            'border-radius:999px; padding:2px 10px; font-size:11px; font-weight:600; '
                            'display:inline-flex; align-items:center; gap:4px;">'
                            '<span class="material-symbols-outlined" style="font-size:13px;">schedule</span>'
                            'Pending</span>',
                            unsafe_allow_html=True
                        )

                with col_size:
                    st.markdown(f"<span style='color:#8b949e; font-size:12px;'>{f['size'] / 1024 / 1024:.2f} MB</span>", unsafe_allow_html=True)

                with col_eye:
                    if st.button("", icon=":material/visibility:", key=f"eye_{idx}_{f['name']}", help="Preview file"):
                        st.session_state.xai_open = None  # close xai to avoid dialog overlap
                        preview_dialog(f)

                with col_x:
                    is_pending = st.session_state.pending_delete == f['name']
                    btn_icon   = ":material/warning:" if is_pending else ":material/close:"
                    btn_help   = "Confirm deletion" if is_pending else "Remove file"

                    if st.button("", icon=btn_icon, key=f"del_{idx}_{f['name']}", type="secondary", help=btn_help):
                        if is_pending:
                            st.session_state.file_manager.pop(idx)
                            st.session_state.pending_delete = None
                            st.session_state.toast_msg  = "File deleted."
                            st.session_state.toast_type = "success"
                            st.rerun()
                        else:
                            st.session_state.pending_delete = f['name']
                            st.rerun()

            # 3s auto revert hack for delete btn
            if st.session_state.pending_delete == f['name']:
                components.html("""
                <script>
                setTimeout(() => {
                    const parent = window.parent.document;
                    const buttons = parent.querySelectorAll("button");
                    buttons.forEach(btn => {
                        if(btn.innerText === "RESET_PENDING_DELETE") {
                            btn.click();
                        }
                    });
                }, 3000);
                </script>
                """, height=0)

        st.write("")

        if st.session_state.is_processing:
            # processing state logic
            files_to_process = [f for f in st.session_state.file_manager
                                 if f['name'] not in st.session_state.processed_startups]
            total        = len(files_to_process)
            progress_bar = st.progress(0)
            status_text  = st.empty()

            for i, f in enumerate(files_to_process):
                file_start  = int((i / total) * 100)
                file_target = int(((i + 0.85) / total) * 100)

                status_text.markdown(
                    f"Analysing **{f['name']}** &nbsp;({i+1}/{total})",
                    unsafe_allow_html=True
                )

                # bg thread for api so ui doesnt freeze completely
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(
                        execute_match_protocol_fn, DummyFile(f), mentors_df, partners_df
                    )

                    current = file_start
                    while not future.done() and current < file_target:
                        remaining = file_target - current
                        increment = random.randint(1, max(1, remaining // 4))
                        current   = min(current + increment, file_target)
                        progress_bar.progress(current)
                        time.sleep(random.uniform(0.18, 0.45))

                    analysis = future.result()

                if analysis:
                    st.session_state.processed_startups[f['name']] = analysis

                # snap progress
                progress_bar.progress(int(((i + 1) / total) * 100))

            # check fails
            actually_processed = sum(
                1 for f in files_to_process if f['name'] in st.session_state.processed_startups
            )
            failed = total - actually_processed

            st.session_state.is_processing = False
            time.sleep(0.4)

            if actually_processed == 0:
                progress_bar.progress(0)
                status_text.markdown("Processing failed. No decks were analysed.")
                st.session_state.toast_msg  = f"Failed to process all {total} file(s). Check your API quota."
                st.session_state.toast_type = "error"
            elif failed > 0:
                status_text.markdown(f"{actually_processed} of {total} processed. {failed} failed.")
                st.session_state.toast_msg  = f"{actually_processed} of {total} deck(s) processed. {failed} failed — check API quota."
                st.session_state.toast_type = "error"
            else:
                progress_bar.progress(100)
                status_text.markdown("All decks processed successfully!")
                st.session_state.toast_msg  = f"{total} deck(s) processed successfully!"
                st.session_state.toast_type = "success"

            time.sleep(0.6)
            st.rerun()

        else:
            # idle state
            new_files = [f for f in st.session_state.file_manager
                         if f['name'] not in st.session_state.processed_startups]
            all_done  = len(new_files) == 0
            btn_label = (
                "All Files Already Analysed"
                if all_done
                else f"Analyse {len(new_files)} New File{'s' if len(new_files) != 1 else ''}"
            )
            _, btn_col, _ = st.columns([1, 2, 1])
            with btn_col:
                if st.button(btn_label, type="primary", use_container_width=True,
                             disabled=all_done,
                             help="All uploaded files have already been analysed." if all_done else None):
                    st.session_state.is_processing = True
                    st.rerun()
