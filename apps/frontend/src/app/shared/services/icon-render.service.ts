import { Injectable, inject } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { getIcon } from '../icons/icon-registry';

@Injectable({ providedIn: 'root' })
export class IconRenderService {
  private readonly sanitizer = inject(DomSanitizer);

  render(key: string, size = 18): SafeHtml {
    return this.sanitizer.bypassSecurityTrustHtml(getIcon(key, size));
  }

  renderSvg(svg: string): SafeHtml {
    return this.sanitizer.bypassSecurityTrustHtml(svg);
  }
}
