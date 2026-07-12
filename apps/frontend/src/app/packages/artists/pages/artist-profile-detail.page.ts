import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { ArtistsApiService } from '../services/artists-api.service';
import { ArtistOrganizationLink, ArtistProfile } from '../models/artist.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

@Component({
  selector: 'app-artist-profile-detail',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule],
  template: `
    <div class="artist-profile-detail-page">
      <a routerLink="/artist-profiles">&larr; Back to list</a>

      @if (artist) {
        <h1>{{ artist.display_name }}</h1>
        <div class="profile-card">
          <div class="field"><label>Status</label>
            <span class="badge" [class]="'badge--' + artist.status">{{ artist.status }}</span>
          </div>
          <div class="field"><label>Legal Name</label><span>{{ artist.legal_name ?? '—' }}</span></div>
          <div class="field"><label>Normalized Name</label><span>{{ artist.normalized_name }}</span></div>
          <div class="field"><label>Warehouse Link</label>
            @if (artist.warehouse_artist_id) {
              <span class="badge badge--linked">Linked to catalog artist #{{ artist.warehouse_artist_id }}</span>
            } @else {
              <span class="badge badge--unlinked">Not linked to catalog</span>
            }
          </div>
        </div>

        <div class="actions">
          @if (artist.status === 'draft' || artist.status === 'inactive') {
            <button class="btn btn--primary" (click)="activate()">Activate</button>
          }
          @if (artist.status === 'active') {
            <button class="btn btn--secondary" (click)="deactivate()">Deactivate</button>
          }
          @if (artist.status !== 'archived') {
            <button class="btn btn--danger" (click)="archive()">Archive</button>
          }
          <a class="btn btn--secondary" [routerLink]="['/artist-profiles', artist.id, 'team']">Manage Team</a>
          <a class="btn btn--secondary" [routerLink]="['/artist-profiles', artist.id, 'history']">View History</a>
        </div>

        <section class="link-warehouse">
          <h2>Warehouse Link</h2>
          <form [formGroup]="warehouseForm" (ngSubmit)="linkWarehouse()">
            <input
              formControlName="warehouse_artist_id"
              type="number"
              placeholder="Catalog artist id"
              class="input"
            />
            <button type="submit" class="btn btn--secondary" [disabled]="warehouseForm.invalid">
              Link
            </button>
          </form>
        </section>

        <section class="transfer">
          <h2>Transfer Organization</h2>
          <form [formGroup]="transferForm" (ngSubmit)="transfer()">
            <input
              formControlName="target_organization_id"
              type="number"
              placeholder="Target organization id"
              class="input"
            />
            <input formControlName="reason" placeholder="Reason (optional)" class="input" />
            <button type="submit" class="btn btn--danger" [disabled]="transferForm.invalid">
              Transfer
            </button>
          </form>
        </section>

        <section class="organizations">
          <h2>Organization Links</h2>
          @if (orgLinks.length === 0) {
            <p>No additional organization links.</p>
          } @else {
            <ul>
              @for (link of orgLinks; track link.id) {
                <li>
                  Org #{{ link.organization_id }} — {{ link.relationship_role }}
                  ({{ link.is_primary ? 'primary' : 'secondary' }}) — {{ link.status }}
                </li>
              }
            </ul>
          }
        </section>
      } @else if (loading) {
        <p>Loading…</p>
      }

      @if (error) {
        <p class="error">{{ error }}</p>
      }
    </div>
  `,
})
export class ArtistProfileDetailPage implements OnInit {
  private api = inject(ArtistsApiService);
  private route = inject(ActivatedRoute);
  private fb = inject(FormBuilder);
  private orgCtx = inject(OrganizationContextService);

  artist: ArtistProfile | null = null;
  orgLinks: ArtistOrganizationLink[] = [];
  loading = false;
  error: string | null = null;

  warehouseForm = this.fb.group({
    warehouse_artist_id: [null as number | null, [Validators.required]],
  });

  transferForm = this.fb.group({
    target_organization_id: [null as number | null, [Validators.required]],
    reason: [''],
  });

  private get orgId(): number {
    return this.orgCtx.activeOrganization()?.id ?? 0;
  }

  private get artistId(): number {
    return Number(this.route.snapshot.paramMap.get('id'));
  }

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    this.api.get(this.orgId, this.artistId).subscribe({
      next: (a) => {
        this.artist = a;
        this.loading = false;
        this.loadOrgLinks();
      },
      error: (e) => {
        this.loading = false;
        this.error = e.error?.message ?? 'Error loading artist profile';
      },
    });
  }

  loadOrgLinks(): void {
    this.api.listOrganizations(this.orgId, this.artistId).subscribe({
      next: (links) => (this.orgLinks = links),
      error: () => (this.orgLinks = []),
    });
  }

  activate(): void {
    this.api.activate(this.orgId, this.artistId).subscribe({
      next: (a) => (this.artist = a),
      error: (e) => (this.error = e.error?.message ?? 'Error activating artist'),
    });
  }

  deactivate(): void {
    this.api.deactivate(this.orgId, this.artistId).subscribe({
      next: (a) => (this.artist = a),
      error: (e) => (this.error = e.error?.message ?? 'Error deactivating artist'),
    });
  }

  archive(): void {
    this.api.archive(this.orgId, this.artistId).subscribe({
      next: (a) => (this.artist = a),
      error: (e) => (this.error = e.error?.message ?? 'Error archiving artist'),
    });
  }

  linkWarehouse(): void {
    if (this.warehouseForm.invalid) return;
    const id = Number(this.warehouseForm.value.warehouse_artist_id);
    this.api.linkWarehouseArtist(this.orgId, this.artistId, id).subscribe({
      next: (a) => {
        this.artist = a;
        this.warehouseForm.reset();
      },
      error: (e) => (this.error = e.error?.message ?? 'Error linking warehouse artist'),
    });
  }

  transfer(): void {
    if (this.transferForm.invalid) return;
    const value = this.transferForm.value;
    this.api
      .transferOrganization(this.orgId, this.artistId, Number(value.target_organization_id), value.reason || undefined)
      .subscribe({
        next: (a) => {
          this.artist = a;
          this.transferForm.reset();
          this.loadOrgLinks();
        },
        error: (e) => (this.error = e.error?.message ?? 'Error transferring artist'),
      });
  }
}
