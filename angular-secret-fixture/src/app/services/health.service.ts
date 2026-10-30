import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface HealthStatus {
  status: string;
  timestamp: string;
  framework: string;
  service: string;
  authenticated: boolean;
}

@Injectable({
  providedIn: 'root',
})
export class HealthService {
  private readonly healthUrl = `${environment.apiUrl}/api/health`;

  constructor(private http: HttpClient) {}

  public checkHealth(token?: string): Observable<HealthStatus> {
    const authToken = token || environment.healthAuthToken;
    const headers = new HttpHeaders({
      Authorization: `Bearer ${authToken}`,
    });

    return this.http.get<HealthStatus>(this.healthUrl, { headers });
  }
}

