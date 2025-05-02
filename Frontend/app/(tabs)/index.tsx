import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  TextInput,
  Pressable,
  StyleSheet,
  Keyboard,
} from "react-native";
import DateTimePickerModal from "react-native-modal-datetime-picker";
import axios from "axios";
import Dropdown from "@/components/Dropdown";

const MainPage = () => {
  const [servicesList, setServicesList] = useState([]);
  const [selectedService, setSelectedService] = useState("");
  const [serviceNum, setServiceNum] = useState("");
  const [stopsList, setStopsList] = useState<string[]>([]);
  const [departureDate, setDepartureDate] = useState(new Date());
  const [departureTime, setDepartureTime] = useState("");
  const [scheduledDeparture, setScheduledDeparture] = useState("");
  const [departureStop, setDepartureStop] = useState("");
  const [isDatePickerVisible, setDatePickerVisibility] = useState(false);
  const [predictedDelay, setPredictedDelay] = useState(null);
  const [origin, setOrigin] = useState("");
  const [originalOrigin, setOriginalOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [originalDestination, setOriginalDestination] = useState("");
  const [directionSelected, setDirectionSelected] = useState(false);
  const [loadingPrediction, setLoadingPrediction] = useState(false);

  useEffect(() => {
    const fetchServices = async () => {
      try {
        const response = await axios.get(
          "https://fetchbusservices.onrender.com/get_services",
          { params: { query: "" } }
        );
        setServicesList(response.data);
      } catch (error) {
        console.error("Error fetching services: ", error);
      }
    };
    fetchServices();
  }, []);

  useEffect(() => {
    const isReady =
      typeof selectedService === 'string' && selectedService.length > 0 &&
      typeof departureStop === 'string' && departureStop.length > 0 &&
      departureDate instanceof Date &&
      typeof departureTime === 'string' && departureTime.length > 0 &&
      typeof destination === 'string' && destination.length > 0 &&
      directionSelected;

    if (isReady) {
      console.log("predictDelay called!")
      predictDelay();
    }
  }, [selectedService, departureStop, departureDate, departureTime, destination]);

  const showDatePicker = () => setDatePickerVisibility(true);
  const hideDatePicker = () => setDatePickerVisibility(false);

  const handleDateConfirm = (date) => {
    setDepartureDate(date);
    hideDatePicker();
  };

  const resetAll = () => {
    setSelectedService("");
    setDepartureStop("");
    setDepartureDate(new Date());
    setDepartureTime("");
    setScheduledDeparture("");
    setDestination("");
    setOriginalDestination("");
    setOrigin("");
    setOriginalOrigin("");
    setStopsList([]);
    setDirectionSelected(false);
    setPredictedDelay(null);
    setServiceNum("");
  }

  const test = () => {
    console.log("Selected service: " + (typeof selectedService === 'string' && selectedService.length > 0));
    console.log("Departure stop: " + (typeof departureStop === 'string' && departureStop.length > 0));
    console.log("Departure date: " + (departureDate instanceof Date));
    console.log("Departure time: " + (typeof departureTime === 'string' && departureTime.length > 0));
    console.log("Destination: " + (typeof destination === 'string' && destination.length > 0));
    console.log("Destination: " + destination);
    console.log("Original Destination: " + originalDestination)
    console.log("Origin: " + origin);
    console.log("Original origin: " + originalOrigin)
  }

  const handleServiceSelect = async (selectedLabel) => {
    const selected = servicesList.find(
      (s) => `${s.number}: ${s.description}` === selectedLabel
    );
    if (!selected) return;

    setSelectedService(selectedLabel);
    setServiceNum(selectedLabel.split(':')[0])
    setDepartureStop("");

    try {
      const response = await axios.get(
        "https://fetchbusservices.onrender.com/get_stops",
        { params: { service_id: selected._id } }
      );
      const stops = response.data;
      setStopsList(stops);

      const org = stops[0];
      const des = stops[stops.length - 1];

      setOriginalOrigin(org);
      setOriginalDestination(des);
      setOrigin(org);
      setDestination(des);
      setDirectionSelected(true);

      console.log(origin)
    } catch (error) {
      console.error("Error fetching stops: ", error);
    }
  };

  const handleStopSelect = (stop) => {
    setDepartureStop(stop);
  };

  const predictDelay = async () => {
    try {
      setLoadingPrediction(true);
      const selected = servicesList.find(
        (s) => `${s.number}: ${s.description}` === selectedService
      );
      if (!selected) return;

      const params = {
        service_id: parseInt(selected._id),
        stop_name: departureStop,
        destination: destination,
        date: departureDate.toISOString().split("T")[0],
        time: departureTime,
      };
      console.log(params)
      const response = await axios.post(
        "https://fetchbusservices.onrender.com/predict_delay",
        params,
        {
          headers: { "Content-Type": "application/json" }
        }
      );
      setPredictedDelay(response.data.predicted_delay_mins);
      setScheduledDeparture(response.data.scheduled_dep);

    } catch (error) {
      console.log("Prediction error:", error);
      setPredictedDelay(null);
    } finally {
      setLoadingPrediction(false);
    }
  };

  const sortedServiceLabels = [...servicesList]
    .sort((a, b) => parseInt(a.number) - parseInt(b.number))
    .map((s) => `${s.number}: ${s.description}`);

  return (
    <View style={{ padding: 16, marginTop: 50 }}>
      {/* Date Picker */}
      <Pressable onPress={showDatePicker}>
        <TextInput
          placeholder="Departure date"
          value={departureDate.toISOString().split("T")[0]}
          editable={false}
          style={styles.inputBox}
        />
      </Pressable>
      <DateTimePickerModal
        isVisible={isDatePickerVisible}
        mode="date"
        date={departureDate}
        onConfirm={handleDateConfirm}
        onCancel={hideDatePicker}
      />

      {/* Time Input */}
      <TextInput
        placeholder="Departure time (HH:MM)"
        value={departureTime}
        onChangeText={setDepartureTime}
        style={styles.inputBox}
      />

      {/* Dropdowns */}
      <Dropdown
        data={sortedServiceLabels}
        placeholder="Search for service"
        onSelect={handleServiceSelect}
        value={selectedService}
      />
      <Dropdown
        data={stopsList}
        placeholder="Search for stop"
        onSelect={handleStopSelect}
        value={departureStop}
      />

      {selectedService && departureStop && departureDate && departureTime && (
        <View style={styles.directionContainer}>
          <Text style={styles.label}>Choose direction of travel:</Text>
          <Pressable
            onPress={() => { setDestination(originalDestination), setDirectionSelected(true) }}
            style={[
              styles.directionButton,
              destination === originalDestination && styles.selectedDirectionBtn
            ]}
          >
            <Text>{stopsList[0]} → {stopsList[stopsList.length - 1]}</Text>
          </Pressable>
          <Pressable
            onPress={() => { setDestination(originalOrigin), setDirectionSelected(true) }}
            style={[
              styles.directionButton,
              destination === originalOrigin && styles.selectedDirectionBtn
            ]}
          >
            <Text>{stopsList[stopsList.length - 1]} → {stopsList[0]}</Text>
          </Pressable>


        </View>
      )}


      {/* Display Selections */}
      {(selectedService || departureStop || destination || scheduledDeparture) && (
        <View style={styles.infoSection}>
          {selectedService && (
            <Text style={styles.infoTitle}>{serviceNum}</Text>
          )}
          {departureStop && (
            <Text>from {departureStop}</Text>
          )}
          {destination && (
            <Text>towards {destination}{'\n'}</Text>
          )}
          {scheduledDeparture && (
            <Text>Scheduled at: {scheduledDeparture}</Text>
          )}
          {(predictedDelay !== null || loadingPrediction) && (
            <View style={styles.resultBox}>
              <Text style={styles.infoTitle}>Expected Punctuality:</Text>
              <Text
                style={[
                  loadingPrediction ? styles.processing : predictedDelay === 0 ? styles.delayOnTime : predictedDelay === null ? styles.processing : predictedDelay <= 5 ? styles.delayMinor : styles.delayMajor
                ]}
              >
                {loadingPrediction ? "Processing..."
                : predictedDelay === 0 ? "On time"
                : predictedDelay === null ? "No journey at this time. Please try another time." 
                : `${predictedDelay} minute${predictedDelay === 1 ? "" : "s"} late` }
              </Text>
            </View>
          )}
        </View>
      )}


      <Pressable
        onPress={resetAll}
        style={styles.button}
      >
        <Text style={styles.label}>Reset</Text>
      </Pressable>

      <Text>Disclaimer: This app provides AI-generated delay estimates based on available historical data. The prediction information is suggestive and should not be taken as definitive. </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  inputBox: {
    padding: 10,
    marginBottom: 10,
    borderRadius: 5,
    borderWidth: 1,
    backgroundColor: "white",
  },
  infoSection: {
    marginTop: 20,
    padding: 10,
    borderWidth: 1,
    borderRadius: 5,
  },
  infoTitle: {
    fontWeight: "bold",
    fontSize: 16,
    marginBottom: 4,
  },
  resultBox: {
    marginTop: 10,
    padding: 10,
    backgroundColor: "#f0f8ff",
    borderRadius: 5,
  },
  directionContainer: {
    marginTop: 20,
    marginBottom: 10,
  },
  button: {
    backgroundColor: "#deb940",
    padding: 12,
    borderRadius: 6,
    alignItems: "center",
    marginTop: 10,
  },
  continueButton: {
    backgroundColor: "#007AFF",
    padding: 12,
    borderRadius: 6,
    alignItems: "center",
    marginTop: 10,
  },
  continueButtonText: {
    color: "white",
    fontWeight: "bold",
  },
  directionButton: {
    padding: 10,
    borderWidth: 1,
    borderColor: "#ccc",
    borderRadius: 6,
    marginTop: 6,
    backgroundColor: "#f5f5f5",
  },
  label: {
    fontWeight: "bold",
    marginBottom: 6,
  },
  selectedDirectionBtn: {
    borderColor: "grey",
    backgroundColor: "#A39B6C"
  },
  delayOnTime: {
    color: "green",
    fontWeight: "bold",
    fontSize: 20,
  },
  delayMinor: {
    color: "orange",
    fontWeight: "bold",
    fontSize: 20,
  },
  delayMajor: {
    color: "red",
    fontWeight: "bold",
    fontSize: 20,
  },
  processing: {
    color: "black",
    fontStyle: "italic",
  }
});

export default MainPage;
