import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getStats(): Observable<any> {
    return this.http.get(`${this.apiUrl}/stats`);
  }

  getArtists(page: number = 1, limit: number = 50): Observable<any> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('limit', limit.toString());
    return this.http.get(`${this.apiUrl}/artists`, { params });
  }

  getTracks(page: number = 1, limit: number = 50, search?: string): Observable<any> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('limit', limit.toString());
    if (search) {
      params = params.set('search', search);
    }
    return this.http.get(`${this.apiUrl}/tracks`, { params });
  }

  getGenres(): Observable<any> {
    return this.http.get(`${this.apiUrl}/genres`);
  }

  getAudioFeatures(): Observable<any> {
    return this.http.get(`${this.apiUrl}/audio-features`);
  }

  getAnalytics(): Observable<any> {
    return this.http.get(`${this.apiUrl}/analytics`);
  }

  getTrending(): Observable<any> {
    return this.http.get(`${this.apiUrl}/trending`);
  }

  getPipeline(): Observable<any> {
    return this.http.get(`${this.apiUrl}/pipeline`);
  }
}
