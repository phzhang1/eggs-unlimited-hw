# Phase 4 — Frontend (`static/index.html`)

## Goal
Replace the Phase 1 placeholder `static/index.html` with a single-page Bootstrap 5 form that submits to `POST /submit`, a table that pulls from `GET /entries` on load and after each submit, and inline error rendering that consumes the `{"errors": [{"field", "message"}]}` shape from Phase 3. After this phase the rubric's UI points are all earnable in the browser.

## Inputs (must read first)
- [AGENTS.md](../AGENTS.md) §6.5 (HTML5 `required` is part of the validation strategy), §6.6 (static HTML + JS, no Jinja2), §6.10 (the error JSON shape this page must consume), §7 (rubric: UI renders without errors, validates required fields, multi-entry, simple grid)
- [hw.md](../hw.md) — `Form fields` for the field set and labels
- [phases/03-endpoints-and-validation.md](03-endpoints-and-validation.md) — the API contract this page is calling

## Deliverables
- `static/index.html` — single file, no separate CSS/JS files. Bootstrap 5 via CDN. Inline `<style>` (only if needed) and inline `<script>`. **Replaces the placeholder; does not add a new file.**

## Page layout
```
+----------------------------------------------+
| Eggs Unlimited — Request Eggs                |
+----------------------------------------------+
| [ Form ]                                     |
|   Farm name *           [____________]       |
|   Contact *             [____________]       |
|   Phone / email         [____________]       |
|   Location *            [____________]       |
|   Type *                [ select v ]          |
|   Size *                [ select v ]          |
|   Grade *               [ select v ]          |
|   Pack *                [ select v ]          |
|   Quantity value *      [____] Unit * [____]  |
|   Price per dozen       [____]                |
|   Available start       [____] End [____]     |
|   Notes                 [_______________]     |
|   [ Submit ]                                  |
| [ Inline status / error region ]              |
+----------------------------------------------+
| Entries                                      |
| | id | farm | contact | type | size | ... |  |
| | .. | ...  | ...     | ...  | ...  | ... |  |
+----------------------------------------------+
```

## Steps
1. Replace `static/index.html` with a complete document. Skeleton:
   ```html
   <!DOCTYPE html>
   <html lang="en">
   <head>
     <meta charset="UTF-8" />
     <meta name="viewport" content="width=device-width, initial-scale=1" />
     <title>Eggs Unlimited — Request Eggs</title>
     <link
       href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
       rel="stylesheet"
     />
   </head>
   <body class="bg-light">
     <main class="container py-4">
       <h1 class="mb-4">Eggs Unlimited — Request Eggs</h1>

       <form id="request-form" novalidate>
         <!-- field rows go here -->
       </form>

       <div id="form-status" class="mt-3" role="status" aria-live="polite"></div>

       <h2 class="h4 mt-5">Entries</h2>
       <div class="table-responsive">
         <table class="table table-striped table-sm" id="entries-table">
           <thead>
             <tr>
               <!-- column headers, see step 4 -->
             </tr>
           </thead>
           <tbody></tbody>
         </table>
       </div>
     </main>

     <script>
       /* Phase 4 JS, see step 5 */
     </script>
   </body>
   </html>
   ```
2. Use Bootstrap's `mb-3` row pattern for each input (`<div class="mb-3"><label class="form-label">...</label><input class="form-control" .../></div>`). Add the `required` HTML5 attribute on every required field — that's the third validation layer per AGENTS.md §6.5 and gives free browser-native error UI for the easy cases.
3. Each `<input>` / `<select>` `name` attribute must match the Pydantic field name **exactly** (`farm_name`, `contact`, `phone_email`, `location`, `type`, `size`, `grade`, `pack`, `quantity_value`, `quantity_unit`, `price_per_dozen`, `available_start`, `available_end`, `notes`). The error-rendering JS uses `name` as its lookup key.
4. Below each input, add an empty `<div class="invalid-feedback" data-error-for="<field-name>"></div>` slot. The JS will populate it when the server returns a 422 for that field.
5. Inline `<script>` should do four things, in this order:
   ```javascript
   const form = document.getElementById("request-form");
   const tbody = document.querySelector("#entries-table tbody");
   const statusBox = document.getElementById("form-status");

   const ENTRY_COLUMNS = [
     "created_at", "farm_name", "contact", "phone_email", "location",
     "type", "size", "grade", "pack",
     "quantity_value", "quantity_unit", "price_per_dozen",
     "available_start", "available_end", "notes",
   ];

   async function loadEntries() {
     const res = await fetch("/entries");
     const rows = await res.json();
     tbody.innerHTML = "";
     for (const row of rows) {
       const tr = document.createElement("tr");
       for (const col of ENTRY_COLUMNS) {
         const td = document.createElement("td");
         td.textContent = row[col] ?? "";
         tr.appendChild(td);
       }
       tbody.appendChild(tr);
     }
   }

   function clearErrors() {
     statusBox.textContent = "";
     statusBox.className = "mt-3";
     for (const el of form.querySelectorAll(".is-invalid")) {
       el.classList.remove("is-invalid");
     }
     for (const el of form.querySelectorAll("[data-error-for]")) {
       el.textContent = "";
     }
   }

   function showErrors(errors) {
     for (const { field, message } of errors) {
       const input = form.querySelector(`[name="${field}"]`);
       const slot = form.querySelector(`[data-error-for="${field}"]`);
       if (input) input.classList.add("is-invalid");
       if (slot) slot.textContent = message;
     }
     statusBox.textContent = "Please fix the errors above.";
     statusBox.className = "mt-3 alert alert-danger";
   }

   form.addEventListener("submit", async (e) => {
     e.preventDefault();
     clearErrors();

     const data = Object.fromEntries(new FormData(form).entries());
     // Coerce numerics — FormData values are always strings.
     for (const k of ["quantity_value", "price_per_dozen"]) {
       if (data[k] === "") delete data[k];
       else if (data[k] != null) data[k] = Number(data[k]);
     }
     // Strip empty-string optionals so Pydantic sees them as missing, not as "".
     for (const k of ["phone_email", "available_start", "available_end", "notes"]) {
       if (data[k] === "") delete data[k];
     }

     const res = await fetch("/submit", {
       method: "POST",
       headers: { "Content-Type": "application/json" },
       body: JSON.stringify(data),
     });
     if (res.status === 201) {
       const { id } = await res.json();
       statusBox.textContent = `Saved entry ${id}.`;
       statusBox.className = "mt-3 alert alert-success";
       form.reset();
       loadEntries();
     } else if (res.status === 422) {
       const { errors } = await res.json();
       showErrors(errors);
     } else {
       statusBox.textContent = `Unexpected server error (${res.status}).`;
       statusBox.className = "mt-3 alert alert-danger";
     }
   });

   loadEntries();
   ```
6. Open the page in a browser with DevTools open:
   - Console must be **clean** — no warnings, no errors. (Bonus rubric point.)
   - Submitting an empty form should trigger HTML5's native required-field popups (`<input required>` doing its job).
   - Submitting with one specific field intentionally bad (e.g., `quantity_value` = "twelve") should show your inline error from the 422 path.
   - After a successful submit, the new row appears in the table without a page reload.
   - Refresh the page; the row is still there (came from `/entries` again).

## Exit criteria
- `static/index.html` is a single self-contained file (no extra `.js`/`.css` files).
- Bootstrap CSS loads from the CDN; no console errors about missing assets.
- Every required field has both `required` (HTML5) and a corresponding `data-error-for` slot.
- Submitting valid data: HTTP 201, success alert appears, table gains a row, form resets.
- Submitting bad data: HTTP 422, each erroring field gets `is-invalid` styling and a per-field message, plus a top-level "Please fix..." alert.
- Browser DevTools console is clean throughout the happy path.
- Refreshing the page re-pulls entries from `/entries` (verifies persistence visible in the UI).

## Walkthrough defense notes
- "Why no React / Vue / HTMX?" — One form + one table doesn't need a framework; adding one means defending a build pipeline I don't need. Vanilla JS is ~50 lines and the reviewer can read every one of them.
- "Why HTML5 `required` *and* Pydantic *and* DB CHECK?" — Defense in depth (AGENTS.md §6.5). HTML5 catches the empty-form case before the request leaves the browser; Pydantic enforces types/required at the API; CHECK is the last-line guard against direct DB writes.
- "Why strip empty strings client-side before POST?" — `FormData` returns `""` for empty optional fields, but Pydantic treats `""` as "the field was provided with value empty-string", not "missing". Stripping makes the optional/required distinction work as the user expects.
- "Why no live entries reload (websocket / polling)?" — Single-user, single-tab; we just call `loadEntries()` after each submit. Anything more would be over-engineering for one form.

## Out of scope for this phase
- **No CSS file.** Inline `<style>` only if absolutely necessary. Bootstrap covers everything we need.
- **No JS bundler / TypeScript / npm.** AGENTS.md §5 vetoes build tooling.
- **No edit / delete buttons** in the entries table — spec doesn't ask for them and they expand the test surface.
- **No client-side filtering / sorting / pagination.**
- **No favicon, no PWA manifest, no service worker.**
- **No accessibility deep-dive beyond `role="status"` + `aria-live`** — but `<label for>` pairing on every input is non-negotiable; Bootstrap's `form-label` class handles styling, not the binding.
