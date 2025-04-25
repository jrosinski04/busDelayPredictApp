import { Image, StyleSheet, Platform } from 'react-native';

import { HelloWave } from '@/components/HelloWave';
import ParallaxScrollView from '@/components/ParallaxScrollView';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';

import axios from "axios";
import React, { useState } from "react";
import ServiceDropdown from '@/components/ServiceDropdown';
import StopDropdown from '@/components/StopDropdown';


const MainPage = () => {
  const [servicesList, setServicesList] = useState([]);
  const [selectedService, setSelectedService] = useState([]);
  const [stopsList, setStopsList] = useState([]);
  const [departureDate, setDepartureDate] = useState("");
  const [departureTime, setDepartureTime] = useState("");
  const [departureStop, setDepartureStop] = useState("");
  const [service, setService] = useState("");

  const handleServiceSelect = async (selectedBus) => {
    try {
      setSelectedService(selectedBus);

      // Getting link for chosen bus service
      const linkResponse = await axios.get(
        'https://fetchbusservices.onrender.com/get_service_link', { params: { query: (selectedBus.Service + "+" + selectedBus.Origin + "+" + selectedBus.Destination) }}
    );

      const serviceLink = linkResponse.data.link;

      // Getting stops from the extracted link
      const stopsResponse = await axios.get("https://fetchbusservices.onrender.com/get_stops", {
        params: { serviceURL: serviceLink }
      });

      const stopsList = stopsResponse.data.stops;
      setStopsList(stopsList);

    } catch (error) {
      console.error("Error fetching stops: ", error);
    }
  };

  const handleStopSelect = async (selectedStop) => {
    try {
      setDepartureStop(selectedStop);

      const response = await fetch('https://fetchbusservices.onrender.com/get_journey_data?serviceURL=${encodeURIComponent(serviceLink)}&stop=${encodedURIComponent(selectedStop)}');
      const data = await response.json();

      console.log("Received journey data: ", data);

    } catch (error) {
      console.error("Error fetching stops or journey data: ", error);
    }
  };

  return (
    <div style={{height: "90%"}}>
      <div style={{display: "flex", justifyContent:"space-between", flexDirection:"column", height:"50%", padding:"0.8rem", outline: "2px solid green"}}>
      <input
        type="date"
        value={departureDate}
        onChange={(e) => setDepartureDate(e.target.value)}
        style={{"display":"block","padding":"0.8rem","margin":"0.6rem","borderRadius":"0.25rem","borderWidth":"1px"}}
      />
      <input
        type="time"
        value={departureTime}
        onChange={(e) => setDepartureTime(e.target.value)}
        style={{"display":"block","padding":"0.8rem","margin":"0.6rem","borderRadius":"0.25rem","borderWidth":"1px"}}
      />
      <ServiceDropdown onSelectService={handleServiceSelect} />
      {Object.keys(selectedService).length > 0 && <p>Selected Service: {selectedService.Service + ": " + selectedService.Origin + " - " + selectedService.Destination}</p>}
      <StopDropdown stops={stopsList} onSelectStop={handleStopSelect} />
      {Object.keys(departureStop).length > 0 && <p>Selected Bus Stop: {departureStop}</p>}

      <div className="border p-4 mt-4">
        <h2 className="font-bold text-lg">Service Number</h2>
        <p>Service origin and destination</p>
        <p>Scheduled departure: <strong>HH:MM</strong></p>
        <p>Estimated delay: <strong>(calculated delay)</strong></p>
      </div>
      </div>
    </div>
  );
}

export default MainPage;


const styles = StyleSheet.create({
  titleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  stepContainer: {
    gap: 8,
    marginBottom: 8,
  },
  reactLogo: {
    height: 178,
    width: 290,
    bottom: 0,
    left: 0,
    position: 'absolute',
  },
});
