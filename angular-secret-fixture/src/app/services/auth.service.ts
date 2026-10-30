import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';

/**
 * Angular Authentication Service.
 * Holds hardcoded client credentials for API interaction.
 */
@Injectable({
  providedIn: 'root',
})
export class AuthService {
  // Hardcoded Client Credentials
  private readonly masterToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fakeAngularClientBearerTokenXyZ777';
  private readonly healthToken = environment.healthAuthToken;

  public getHealthAuthToken(): string {
    return this.healthToken;
  }

  public getMasterBearerToken(): string {
    return this.masterToken;
  }

  public isAuthenticated(): boolean {
    return Boolean(this.healthToken);
  }
}

