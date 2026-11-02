# Roster Editing and TXT Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let teachers edit and delete students in the current roster and export the edited roster as a UTF-8 TXT file.

**Architecture:** Keep the existing Treeview and add selected-row edit/delete actions plus a Save As export action. Student rename/delete operations update the in-memory roster, fixed-seat rules, and current seating before using the existing persistence and refresh functions.

**Tech Stack:** Python 3, Tkinter/ttk, `pathlib` and standard library dialogs.

**Spec:** `docs/superpowers/specs/2026-11-02-roster-edit-export-design.md`

## Global Constraints

- Keep the existing Python/Tkinter application and add no external packages.
- Reject blank or duplicate names.
- Preserve roster order when exporting one UTF-8 name per line.
- Renaming carries the student's current and fixed seat references to the new name.
- Deleting removes the student's current and fixed seat references.

## Review Focus

- Blank or whitespace-only replacement names must leave the roster unchanged.
- A duplicate replacement name must be rejected without changing seating or fixed-seat rules.
- Renaming a student with a current seat and a fixed seat must update both references.
- Deleting a student must clear only that student's references and keep other students' seats intact.
- Exporting an empty roster or a name with Korean characters must write a valid UTF-8 text file.

---

### Task 1: Add roster edit and delete behavior

**Files:**
- Modify: `seat_allocator.py` (`SeatAllocatorApp` roster operations)

**Interfaces:**
- Produces: `_rename_student(old_name: str, new_name: str) -> bool` and `_delete_student(name: str) -> bool`.
- A successful operation updates `self.names`, `self.fixed`, and `self.seating`, persists with `_persist()`, refreshes with `_refresh_all()`, and returns `True`; invalid or missing inputs return `False` without mutation.

- [ ] Implement name normalization and blank/duplicate checks in `_rename_student`.
- [ ] Transfer a renamed student's fixed-seat key and each current seating value from the old name to the new name.
- [ ] Remove the deleted student's roster entry, fixed-seat key, and current seating entry in `_delete_student` without changing other seat assignments.
- [ ] Review the above input conditions against the implementation before continuing.

### Task 2: Add roster editing controls

**Files:**
- Modify: `seat_allocator.py` (`_build_roster`, add/edit/delete dialog handlers, animation state)

**Interfaces:**
- Selection source: the existing `self.roster_tree` single selected row.
- The edit handler prompts with the selected name as the initial value and calls `_rename_student`.
- The delete handler confirms removal and calls `_delete_student`.

- [ ] Add `수정` and `삭제` controls beside the existing add/import controls.
- [ ] Require a selected row for edit/delete and show a concise prompt when none is selected.
- [ ] Confirm deletion before removing a student.
- [ ] Disable roster mutation controls during the seating animation and restore them when the animation completes.
- [ ] Review that the selection, confirmation, and disabled-animation paths preserve the existing roster order and seat references.

### Task 3: Export the current roster

**Files:**
- Modify: `seat_allocator.py` (`_build_roster`, `_export_names`)

**Interfaces:**
- `_export_names() -> None` opens `filedialog.asksaveasfilename`, writes the current `self.names` in order as UTF-8 with one name per line, and reports write errors through the existing Tk message-box pattern.

- [ ] Add a `명단 TXT로 저장` control.
- [ ] Write selected output using UTF-8 and preserve current roster order, including Korean names.
- [ ] Handle dialog cancellation without changing app state and show file-write failures to the user.
- [ ] Review empty-roster and non-ASCII export behavior from the code path.

### Task 4: Document roster controls

**Files:**
- Modify: `README.md`

- [ ] Document selecting a roster row to edit/delete and saving the edited list as TXT.
- [ ] Keep the existing import instructions and persistence behavior accurate.
