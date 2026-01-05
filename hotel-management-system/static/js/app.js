const toPersianDigits = (s) =>
  String(s).replace(/\d/g, d => "۰۱۲۳۴۵۶۷۸۹"[d]);

function formatPersianDate(isoDate) {
  if (!isoDate) return "";
  const d = new Date(isoDate);
  if (isNaN(d.getTime())) {
    const parts = String(isoDate).split("-");
    if (parts.length === 3) {
      const d2 = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
      if (!isNaN(d2.getTime())) return new Intl.DateTimeFormat("fa-IR", { dateStyle: "medium" }).format(d2);
    }
    return String(isoDate);
  }
  return new Intl.DateTimeFormat("fa-IR", { dateStyle: "medium" }).format(d);
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".persian-date").forEach(el => {
    const v = el.getAttribute("data-date");
    el.textContent = formatPersianDate(v);
  });

  document.querySelectorAll(".persian-digits").forEach(el => {
    el.textContent = toPersianDigits(el.textContent);
  });

  const q = document.getElementById("tableSearch");
  const table = document.getElementById("dataTable");
  if (q && table) {
    q.addEventListener("input", () => {
      const term = q.value.toLowerCase();
      table.querySelectorAll("tbody tr").forEach(tr => {
        tr.style.display = tr.textContent.toLowerCase().includes(term) ? "" : "none";
      });
    });
  }

  document.querySelectorAll(".confirm-delete").forEach(a => {
    a.addEventListener("click", (e) => {
      if (!confirm("مطمئنی حذف شود؟")) e.preventDefault();
    });
  });
  document.querySelectorAll(".confirm-action").forEach(a => {
    a.addEventListener("click", (e) => {
      const msg = a.getAttribute("data-confirm") || "مطمئنی؟";
      if (!confirm(msg)) e.preventDefault();
    });
  });
});
