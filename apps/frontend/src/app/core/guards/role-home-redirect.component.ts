import { Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { PostAuthOrchestrator } from '../spaces/post-auth.orchestrator';

/** Authenticated `/` — navigates through the same post-auth orchestrator as login. */
@Component({
  selector: 'app-role-home-redirect',
  standalone: true,
  template: '',
})
export class RoleHomeRedirectComponent implements OnInit {
  private readonly orchestrator = inject(PostAuthOrchestrator);
  private readonly router = inject(Router);

  ngOnInit(): void {
    void this.orchestrator.goAfterAuthenticated().catch(() => {
      // Bootstrap failed — login owns the retry surface.
      void this.router.navigateByUrl('/login');
    });
  }
}
