import { Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { homePathForRole } from '../navigation/nav-access.policy';
import { AuthService } from '../services/auth.service';

/** Tiny landing for authenticated `/` — navigates to role home. */
@Component({
  selector: 'app-role-home-redirect',
  standalone: true,
  template: '',
})
export class RoleHomeRedirectComponent implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  ngOnInit(): void {
    void this.router.navigateByUrl(homePathForRole(this.auth.role()), { replaceUrl: true });
  }
}
