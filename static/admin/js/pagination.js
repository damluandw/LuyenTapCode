/**
 * Pagination Helper Component
 * Provides consistent pagination UI and logic across admin pages
 */
class PaginationHelper {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    this.currentPage = 1;
    this.pageSize = options.pageSize || 10;
    this.totalItems = 0;
    this.data = [];
    this.renderCallback = options.renderCallback;
    this.pageSizeOptions = options.pageSizeOptions || [5, 10, 20, 50, 100];
    this.instanceName = options.instanceName || "window.paginationInstance";
  }

  setData(data) {
    this.data = data;
    this.totalItems = data.length;
    this.currentPage = 1;
    this.render();
  }

  get totalPages() {
    return Math.ceil(this.totalItems / this.pageSize);
  }

  get currentPageData() {
    const start = (this.currentPage - 1) * this.pageSize;
    const end = start + this.pageSize;
    return this.data.slice(start, end);
  }

  goToPage(page) {
    if (page < 1 || page > this.totalPages) return;
    this.currentPage = page;
    this.render();
  }

  changePageSize(newSize) {
    this.pageSize = parseInt(newSize);
    this.currentPage = 1;
    this.render();
  }

  render() {
    if (this.renderCallback) {
      this.renderCallback(this.currentPageData);
    }
    this.renderPaginationControls();
  }

  renderPaginationControls() {
    if (!this.container) return;

    const totalPages = this.totalPages;
    if (totalPages === 0) {
      this.container.innerHTML = '';
      return;
    }

    let html = `
      <div class="d-flex justify-content-between align-items-center flex-wrap gap-3">
        <div class="text-muted small">
          Hiển thị ${(this.currentPage - 1) * this.pageSize + 1} - 
          ${Math.min(this.currentPage * this.pageSize, this.totalItems)} 
          trong tổng số ${this.totalItems}
        </div>
        
        <div class="d-flex gap-2 align-items-center">
          <select class="form-select form-select-sm" style="width: auto" 
                  onchange="${this.instanceName}?.changePageSize(this.value)">
            ${this.pageSizeOptions.map(size => 
              `<option value="${size}" ${size === this.pageSize ? 'selected' : ''}>
                ${size} / trang
              </option>`
            ).join('')}
          </select>

          <nav>
            <ul class="pagination pagination-sm mb-0">
              <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="${this.instanceName}?.goToPage(${this.currentPage - 1}); return false;">
                  <i class="bi bi-chevron-left"></i>
                </a>
              </li>
    `;

    // Page numbers
    const maxVisible = 5;
    let startPage = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    
    if (endPage - startPage < maxVisible - 1) {
      startPage = Math.max(1, endPage - maxVisible + 1);
    }

    if (startPage > 1) {
      html += `<li class="page-item"><a class="page-link" href="#" onclick="${this.instanceName}?.goToPage(1); return false;">1</a></li>`;
      if (startPage > 2) {
        html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
      }
    }

    for (let i = startPage; i <= endPage; i++) {
      html += `
        <li class="page-item ${i === this.currentPage ? 'active' : ''}">
          <a class="page-link" href="#" onclick="${this.instanceName}?.goToPage(${i}); return false;">${i}</a>
        </li>
      `;
    }

    if (endPage < totalPages) {
      if (endPage < totalPages - 1) {
        html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
      }
      html += `<li class="page-item"><a class="page-link" href="#" onclick="${this.instanceName}?.goToPage(${totalPages}); return false;">${totalPages}</a></li>`;
    }

    html += `
              <li class="page-item ${this.currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="${this.instanceName}?.goToPage(${this.currentPage + 1}); return false;">
                  <i class="bi bi-chevron-right"></i>
                </a>
              </li>
            </ul>
          </nav>
        </div>
      </div>
    `;

    this.container.innerHTML = html;
  }
}
